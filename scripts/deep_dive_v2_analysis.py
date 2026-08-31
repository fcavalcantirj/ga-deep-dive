"""
GA4 DEEP DIVE v2 — ANALYSIS MODULES
Snapshot schema, per-topic GA4 analysis functions, and health scoring.
"""

from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass, asdict

from deep_dive_v2_client import GA4Client
from deep_dive_v2_config import SOLVR_CONTENT_GROUPS
from deep_dive_v2_utils import safe_int, safe_float

# ============================================================================
# ANALYSIS MODULES
# ============================================================================

@dataclass
class Snapshot:
    """Complete analytics snapshot for storage/comparison."""
    property_id: str
    property_name: str
    generated_at: str
    period_days: int

    # Core metrics
    sessions: int = 0
    users: int = 0
    new_users: int = 0
    engagement_rate: float = 0.0
    bounce_rate: float = 0.0
    avg_duration: float = 0.0
    pages_per_session: float = 0.0
    page_views: int = 0
    events: int = 0

    # Activity metrics
    dau: int = 0
    wau: int = 0
    mau: int = 0

    # Traffic sources (top 5)
    top_channels: List[Dict] = None
    top_sources: List[Dict] = None

    # Content performance
    top_pages: List[Dict] = None
    top_landing: List[Dict] = None
    high_bounce_pages: List[Dict] = None

    # Geography
    top_countries: List[Dict] = None

    # Technology
    device_split: Dict = None
    browser_split: Dict = None

    # Solvr-specific
    content_groups: Dict = None

    # Health scores
    scores: Dict = None
    overall_score: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


def analyze_core_metrics(ga: GA4Client, days: int) -> Dict:
    """Core metrics with period comparison."""

    # Current period
    current = ga.metrics_only([
        "sessions", "totalUsers", "newUsers", "activeUsers",
        "engagedSessions", "engagementRate", "bounceRate",
        "averageSessionDuration", "screenPageViews", "eventCount"
    ], days=days)

    current2 = ga.metrics_only([
        "sessionsPerUser", "screenPageViewsPerSession", "eventsPerSession",
        "userEngagementDuration"
    ], days=days)

    # Previous period (for comparison) - use explicit dates
    today = datetime.now()
    end_prev = (today - timedelta(days=days+1)).strftime("%Y-%m-%d")
    start_prev = (today - timedelta(days=days*2)).strftime("%Y-%m-%d")

    previous = ga.report([], [
        "sessions", "totalUsers", "newUsers", "engagementRate",
        "bounceRate", "averageSessionDuration", "screenPageViews"
    ], start_date=start_prev, end_date=end_prev, limit=1)
    prev = previous[0] if previous and '_error' not in previous[0] else {}

    return {
        'current': {**current, **current2},
        'previous': prev
    }


def analyze_acquisition(ga: GA4Client, days: int) -> Dict:
    """Full acquisition breakdown."""

    # Channel groups
    channels = ga.report(
        ["sessionDefaultChannelGroup"],
        ["sessions", "totalUsers", "newUsers", "engagementRate", "bounceRate", "conversions"],
        days=days, limit=15, order_by="sessions"
    )

    # Source/Medium detail
    sources = ga.report(
        ["sessionSource", "sessionMedium"],
        ["sessions", "totalUsers", "engagementRate", "averageSessionDuration"],
        days=days, limit=25, order_by="sessions"
    )

    # Referrers with URLs
    referrers = ga.report(
        ["sessionSource", "pageReferrer"],
        ["sessions", "engagementRate"],
        days=days, limit=30, order_by="sessions"
    )

    # First user source (how they first found us)
    first_source = ga.report(
        ["firstUserSource", "firstUserMedium"],
        ["totalUsers", "newUsers", "engagementRate"],
        days=days, limit=15, order_by="totalUsers"
    )

    return {
        'channels': channels,
        'sources': sources,
        'referrers': referrers,
        'first_source': first_source
    }


def analyze_content(ga: GA4Client, days: int, is_solvr: bool = False) -> Dict:
    """Content performance analysis."""

    # All pages - GA4 valid metrics only
    pages = ga.report(
        ["pagePath", "pageTitle"],
        ["screenPageViews", "totalUsers", "engagementRate",
         "averageSessionDuration", "bounceRate"],
        days=days, limit=50, order_by="screenPageViews"
    )

    # Landing pages
    landing = ga.report(
        ["landingPage"],
        ["sessions", "totalUsers", "bounceRate", "engagementRate",
         "averageSessionDuration", "screenPageViewsPerSession"],
        days=days, limit=30, order_by="sessions"
    )

    # Exit pages - Note: GA4 doesn't have exits metric, use sessions instead
    exits = ga.report(
        ["pagePath"],
        ["sessions", "screenPageViews", "bounceRate"],
        days=days, limit=20, order_by="sessions"
    )
    # Use bounce rate as proxy for exit-prone pages
    for e in exits:
        if '_error' not in e:
            e['exitRate'] = safe_float(e.get('bounceRate', 0))

    # High bounce pages (problem areas)
    high_bounce = [p for p in pages if '_error' not in p
                   and safe_float(p.get('bounceRate', 0)) > 0.6
                   and safe_int(p.get('screenPageViews', 0)) > 5]
    high_bounce.sort(key=lambda x: safe_float(x.get('bounceRate', 0)), reverse=True)

    result = {
        'pages': pages,
        'landing': landing,
        'exits': exits[:15],
        'high_bounce': high_bounce[:10]
    }

    # Solvr-specific content groups
    if is_solvr:
        groups = {}
        for group_name, patterns in SOLVR_CONTENT_GROUPS.items():
            group_pages = [p for p in pages if '_error' not in p
                          and any(p.get('pagePath', '').startswith(pat) for pat in patterns)]
            if group_pages:
                groups[group_name] = {
                    'pages': len(group_pages),
                    'views': sum(safe_int(p.get('screenPageViews', 0)) for p in group_pages),
                    'users': sum(safe_int(p.get('totalUsers', 0)) for p in group_pages),
                    'avg_engagement': sum(safe_float(p.get('engagementRate', 0)) for p in group_pages) / len(group_pages)
                }
        result['content_groups'] = groups

    return result


def analyze_users(ga: GA4Client, days: int) -> Dict:
    """User behavior analysis."""

    # New vs returning
    new_vs_ret = ga.report(
        ["newVsReturning"],
        ["sessions", "totalUsers", "engagementRate", "bounceRate",
         "screenPageViewsPerSession", "averageSessionDuration"],
        days=days, limit=5
    )

    # User activity metrics
    activity = ga.metrics_only([
        "active1DayUsers", "active7DayUsers", "active28DayUsers",
        "dauPerMau", "dauPerWau", "wauPerMau"
    ], days=days)

    # Session engagement
    # Note: engagedSessions is sessions > 10s OR had conversion OR 2+ page views
    engaged = ga.metrics_only([
        "sessions", "engagedSessions", "engagementRate",
        "averageSessionDuration", "screenPageViewsPerSession"
    ], days=days)

    # User languages
    languages = ga.report(
        ["language"],
        ["totalUsers", "sessions", "engagementRate"],
        days=days, limit=15, order_by="totalUsers"
    )

    return {
        'new_vs_returning': new_vs_ret,
        'activity': activity,
        'engagement': engaged,
        'languages': languages
    }


def analyze_geography(ga: GA4Client, days: int) -> Dict:
    """Geography breakdown."""

    countries = ga.report(
        ["country"],
        ["sessions", "totalUsers", "newUsers", "engagementRate", "averageSessionDuration"],
        days=days, limit=20, order_by="sessions"
    )

    cities = ga.report(
        ["country", "city", "region"],
        ["sessions", "totalUsers", "engagementRate"],
        days=days, limit=30, order_by="sessions"
    )

    return {
        'countries': countries,
        'cities': cities
    }


def analyze_technology(ga: GA4Client, days: int) -> Dict:
    """Technology breakdown."""

    # Devices
    devices = ga.report(
        ["deviceCategory"],
        ["sessions", "totalUsers", "engagementRate", "bounceRate"],
        days=days, limit=5, order_by="sessions"
    )

    # Browsers
    browsers = ga.report(
        ["browser"],
        ["sessions", "totalUsers", "engagementRate", "bounceRate"],
        days=days, limit=10, order_by="sessions"
    )

    # OS
    os_data = ga.report(
        ["operatingSystem"],
        ["sessions", "totalUsers", "engagementRate"],
        days=days, limit=10, order_by="sessions"
    )

    # Screen resolutions (useful for design)
    screens = ga.report(
        ["screenResolution", "deviceCategory"],
        ["sessions", "totalUsers"],
        days=days, limit=15, order_by="sessions"
    )

    # Mobile models (if significant mobile traffic)
    mobile_models = ga.report(
        ["mobileDeviceModel", "operatingSystem"],
        ["sessions", "totalUsers"],
        days=days, limit=10, order_by="sessions"
    )

    return {
        'devices': devices,
        'browsers': browsers,
        'os': os_data,
        'screens': screens,
        'mobile_models': mobile_models
    }


def analyze_time_patterns(ga: GA4Client, days: int) -> Dict:
    """Time-based patterns."""

    # Hour of day
    hourly = ga.report(
        ["hour"],
        ["sessions", "totalUsers", "engagementRate"],
        days=days, limit=24
    )
    hourly = sorted([h for h in hourly if '_error' not in h], key=lambda x: int(x['hour']))

    # Day of week
    daily = ga.report(
        ["dayOfWeek"],
        ["sessions", "totalUsers", "engagementRate", "averageSessionDuration"],
        days=days, limit=7
    )
    daily = sorted([d for d in daily if '_error' not in d], key=lambda x: int(x['dayOfWeek']))

    # Daily trend
    trend = ga.report(
        ["date"],
        ["sessions", "totalUsers", "newUsers", "engagementRate", "screenPageViews"],
        days=days, limit=days+1
    )
    trend = sorted([t for t in trend if '_error' not in t], key=lambda x: x['date'])

    return {
        'hourly': hourly,
        'daily': daily,
        'trend': trend
    }


def analyze_events(ga: GA4Client, days: int) -> Dict:
    """Event tracking analysis."""

    events = ga.report(
        ["eventName"],
        ["eventCount", "totalUsers", "eventCountPerUser", "eventValue"],
        days=days, limit=30, order_by="eventCount"
    )

    # Key events (conversions)
    conversions = ga.report(
        ["eventName"],
        ["conversions", "totalUsers"],
        days=days, limit=20, order_by="conversions"
    )
    conversions = [c for c in conversions if '_error' not in c and safe_int(c.get('conversions', 0)) > 0]

    return {
        'events': events,
        'conversions': conversions
    }


def calculate_health_scores(data: Dict) -> Dict:
    """Calculate health scores based on all data."""

    scores = {}

    # 1. Engagement Score (0-100)
    core = data.get('core', {}).get('current', {})
    eng_rate = safe_float(core.get('engagementRate', 0))
    duration = safe_float(core.get('averageSessionDuration', 0))
    pps = safe_float(core.get('screenPageViewsPerSession', 0))

    # Engagement: 40% rate + 30% duration (target 3min) + 30% pages (target 4)
    eng_score = eng_rate * 40 + min(duration/180, 1) * 30 + min(pps/4, 1) * 30
    scores['engagement'] = int(min(100, eng_score))

    # 2. Traffic Diversity (0-100)
    channels = data.get('acquisition', {}).get('channels', [])
    if channels:
        total = sum(safe_int(c.get('sessions', 0)) for c in channels if '_error' not in c)
        top = safe_int(channels[0].get('sessions', 0)) if channels else 0
        diversity = 1 - (top / total) if total > 0 else 0
        scores['traffic_diversity'] = int(diversity * 100)
    else:
        scores['traffic_diversity'] = 50

    # 3. Mobile Readiness (0-100)
    devices = data.get('technology', {}).get('devices', [])
    if devices:
        total = sum(safe_int(d.get('sessions', 0)) for d in devices if '_error' not in d)
        mobile = sum(safe_int(d.get('sessions', 0)) for d in devices
                    if '_error' not in d and d.get('deviceCategory') in ['mobile', 'tablet'])
        mobile_pct = mobile / total if total > 0 else 0
        # Good mobile = 30-60% of traffic
        if 0.3 <= mobile_pct <= 0.6:
            scores['mobile'] = 90
        elif mobile_pct > 0.1:
            scores['mobile'] = 70
        else:
            scores['mobile'] = 40
    else:
        scores['mobile'] = 50

    # 4. Content Quality (0-100)
    content = data.get('content', {})
    high_bounce = content.get('high_bounce', [])
    total_pages = len(content.get('pages', []))
    problem_ratio = len(high_bounce) / total_pages if total_pages > 0 else 0
    scores['content'] = int(max(0, 100 - problem_ratio * 200))

    # 5. Growth (0-100)
    core_current = data.get('core', {}).get('current', {})
    core_prev = data.get('core', {}).get('previous', {})
    curr_sessions = safe_int(core_current.get('sessions', 0))
    prev_sessions = safe_int(core_prev.get('sessions', 0))

    if prev_sessions > 0:
        growth = (curr_sessions - prev_sessions) / prev_sessions
        # +50% = 100, 0% = 50, -50% = 0
        scores['growth'] = int(min(100, max(0, 50 + growth * 100)))
    else:
        scores['growth'] = 75 if curr_sessions > 0 else 50

    # 6. Retention (0-100)
    activity = data.get('users', {}).get('activity', {})
    dau = safe_int(activity.get('active1DayUsers', 0))
    mau = safe_int(activity.get('active28DayUsers', 0))
    if mau > 0:
        stickiness = dau / mau
        # 20% stickiness = excellent for most products
        scores['retention'] = int(min(100, stickiness * 500))
    else:
        scores['retention'] = 50

    return scores
