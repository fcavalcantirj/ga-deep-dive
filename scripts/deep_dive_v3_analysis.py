"""
GA4 DEEP DIVE v3 — ANALYSIS MODULES
Per-topic GA4 analysis functions and health scoring for the v3 CLI.
"""

import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict

from deep_dive_v3_client import GA4
from deep_dive_v3_utils import safe_int, safe_float

# ============================================================================
# ANALYSIS MODULES
# ============================================================================

def analyze_executive(ga: GA4, days: int) -> Dict:
    """Executive summary with period comparison."""

    # This period - split into 2 queries (GA4 limit: 10 metrics)
    current1 = ga.totals([
        "sessions", "totalUsers", "newUsers", "engagedSessions",
        "engagementRate", "bounceRate", "averageSessionDuration",
        "screenPageViews", "eventCount"
    ], days)

    current2 = ga.totals([
        "sessionsPerUser", "screenPageViewsPerSession"
    ], days)

    current = {**current1, **current2}

    # Previous period
    today = datetime.now()
    prev_end = (today - timedelta(days=days+1)).strftime("%Y-%m-%d")
    prev_start = (today - timedelta(days=days*2+1)).strftime("%Y-%m-%d")
    previous = ga.query([], [
        "sessions", "totalUsers", "newUsers", "engagementRate",
        "bounceRate", "averageSessionDuration", "screenPageViews"
    ], start=prev_start, end=prev_end, limit=1)
    prev = previous[0] if previous and "_error" not in previous[0] else {}

    # Activity metrics
    activity = ga.totals(["active1DayUsers", "active7DayUsers", "active28DayUsers"], days)

    return {"current": current, "previous": prev, "activity": activity}


def analyze_acquisition_deep(ga: GA4, days: int) -> Dict:
    """Deep acquisition analysis with attribution."""

    # Channel performance with engagement
    channels = ga.query(
        ["sessionDefaultChannelGroup"],
        ["sessions", "totalUsers", "newUsers", "engagedSessions",
         "engagementRate", "bounceRate", "averageSessionDuration",
         "screenPageViewsPerSession", "conversions"],
        days=days, limit=20, order="sessions"
    )

    # Source/Medium detail
    sources = ga.query(
        ["sessionSource", "sessionMedium"],
        ["sessions", "totalUsers", "newUsers", "engagementRate",
         "bounceRate", "averageSessionDuration"],
        days=days, limit=30, order="sessions"
    )

    # First user source (acquisition attribution)
    first_touch = ga.query(
        ["firstUserSource", "firstUserMedium", "firstUserCampaignName"],
        ["totalUsers", "newUsers", "engagementRate", "averageSessionDuration"],
        days=days, limit=20, order="totalUsers"
    )

    # Session source (last touch)
    last_touch = ga.query(
        ["sessionSource", "sessionMedium", "sessionCampaignName"],
        ["sessions", "engagedSessions", "conversions"],
        days=days, limit=20, order="sessions"
    )

    # Referrer URLs (actual links)
    referrers = ga.query(
        ["pageReferrer"],
        ["sessions", "totalUsers", "engagementRate"],
        days=days, limit=25, order="sessions"
    )

    return {
        "channels": channels,
        "sources": sources,
        "first_touch": first_touch,
        "last_touch": last_touch,
        "referrers": referrers
    }


def analyze_geography_deep(ga: GA4, days: int) -> Dict:
    """Geography analysis - find your gold mine countries."""

    # Country overview
    countries = ga.query(
        ["country"],
        ["sessions", "totalUsers", "newUsers", "engagedSessions",
         "engagementRate", "bounceRate", "averageSessionDuration",
         "screenPageViewsPerSession", "conversions"],
        days=days, limit=30, order="sessions"
    )

    # City detail (top 30)
    cities = ga.query(
        ["country", "city"],
        ["sessions", "totalUsers", "engagementRate", "averageSessionDuration"],
        days=days, limit=40, order="sessions"
    )

    # Language distribution
    languages = ga.query(
        ["language"],
        ["totalUsers", "sessions", "engagementRate"],
        days=days, limit=15, order="totalUsers"
    )

    # Calculate country quality score (engagement * sessions weight)
    for c in countries:
        if "_error" not in c:
            eng = safe_float(c.get("engagementRate", 0))
            sess = safe_int(c.get("sessions", 0))
            dur = safe_float(c.get("averageSessionDuration", 0))
            # Quality = engagement rate * log(sessions) * duration factor
            c["quality_score"] = eng * math.log(max(sess, 1) + 1) * min(dur/60, 5)

    return {
        "countries": countries,
        "cities": cities,
        "languages": languages
    }


def analyze_content_deep(ga: GA4, days: int, is_solvr: bool = False) -> Dict:
    """Content analysis - what's working, what's not."""

    # Page performance
    pages = ga.query(
        ["pagePath"],
        ["screenPageViews", "totalUsers", "engagementRate",
         "bounceRate", "averageSessionDuration"],
        days=days, limit=50, order="screenPageViews"
    )

    # Landing pages (entry points)
    landing = ga.query(
        ["landingPage"],
        ["sessions", "totalUsers", "newUsers", "bounceRate",
         "engagementRate", "averageSessionDuration", "screenPageViewsPerSession"],
        days=days, limit=30, order="sessions"
    )

    # Page trends (this week vs last week)
    this_week = ga.query(
        ["pagePath"],
        ["screenPageViews", "totalUsers"],
        days=7, limit=30, order="screenPageViews"
    )
    last_week_end = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
    last_week_start = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    last_week = ga.query(
        ["pagePath"],
        ["screenPageViews", "totalUsers"],
        start=last_week_start, end=last_week_end, limit=30, order="screenPageViews"
    )

    # Calculate trends
    last_week_map = {p["pagePath"]: safe_int(p["screenPageViews"])
                     for p in last_week if "_error" not in p}
    for p in this_week:
        if "_error" not in p:
            curr = safe_int(p["screenPageViews"])
            prev = last_week_map.get(p["pagePath"], 0)
            p["trend"] = ((curr - prev) / prev * 100) if prev > 0 else (100 if curr > 0 else 0)

    # High bounce pages (problem areas)
    high_bounce = [p for p in pages if "_error" not in p
                   and safe_float(p.get("bounceRate", 0)) > 0.6
                   and safe_int(p.get("screenPageViews", 0)) > 3]

    result = {
        "pages": pages,
        "landing": landing,
        "trending": sorted([p for p in this_week if "_error" not in p],
                          key=lambda x: x.get("trend", 0), reverse=True)[:10],
        "declining": sorted([p for p in this_week if "_error" not in p],
                           key=lambda x: x.get("trend", 0))[:10],
        "high_bounce": sorted(high_bounce, key=lambda x: safe_float(x.get("bounceRate", 0)), reverse=True)[:10]
    }

    # Solvr content groups
    if is_solvr:
        groups = defaultdict(lambda: {"views": 0, "users": 0, "engagement": [], "pages": 0})
        for p in pages:
            if "_error" in p: continue
            path = p.get("pagePath", "")

            # Categorize
            if path.startswith("/agents"): cat = "agents"
            elif path.startswith("/problems") or path.startswith("/problem/"): cat = "problems"
            elif path.startswith("/ideas") or path.startswith("/idea/"): cat = "ideas"
            elif path.startswith("/questions"): cat = "questions"
            elif path == "/feed": cat = "feed"
            elif path in ["/login", "/join"] or path.startswith("/auth"): cat = "auth"
            elif path.startswith("/settings"): cat = "settings"
            elif path.startswith("/api"): cat = "api"
            elif path == "/": cat = "home"
            else: cat = "other"

            groups[cat]["views"] += safe_int(p.get("screenPageViews", 0))
            groups[cat]["users"] += safe_int(p.get("totalUsers", 0))
            groups[cat]["engagement"].append(safe_float(p.get("engagementRate", 0)))
            groups[cat]["pages"] += 1

        # Calculate averages
        for cat, data in groups.items():
            if data["engagement"]:
                data["avg_engagement"] = sum(data["engagement"]) / len(data["engagement"])
            else:
                data["avg_engagement"] = 0
            del data["engagement"]

        result["content_groups"] = dict(groups)

    return result


def analyze_events_deep(ga: GA4, days: int) -> Dict:
    """Event analysis - what do users actually DO."""

    # All events
    events = ga.query(
        ["eventName"],
        ["eventCount", "totalUsers", "eventCountPerUser"],
        days=days, limit=30, order="eventCount"
    )

    # Events by engaged users vs all
    engaged_events = ga.query(
        ["eventName"],
        ["eventCount", "totalUsers"],
        days=days, limit=20, order="eventCount"
    )

    # Custom events (non-automatic)
    auto_events = {"page_view", "scroll", "session_start", "first_visit",
                   "user_engagement", "click", "file_download", "view_search_results"}
    custom = [e for e in events if "_error" not in e
              and e.get("eventName") not in auto_events]

    # Event sequences (what happens after page_view)
    # Note: GA4 doesn't give sequences directly, but we can infer from counts

    return {
        "events": events,
        "custom_events": custom,
        "event_participation": {
            e["eventName"]: safe_int(e["totalUsers"])
            for e in events if "_error" not in e
        }
    }


def analyze_user_segments(ga: GA4, days: int) -> Dict:
    """User segmentation - find your power users."""

    # New vs returning
    new_ret = ga.query(
        ["newVsReturning"],
        ["sessions", "totalUsers", "engagedSessions", "engagementRate",
         "bounceRate", "screenPageViewsPerSession", "averageSessionDuration"],
        days=days, limit=5
    )

    # By session count (frequency)
    session_count = ga.query(
        ["sessionDefaultChannelGroup"],  # Proxy for user segments
        ["sessions", "totalUsers", "engagedSessions", "engagementRate"],
        days=days, limit=10, order="sessions"
    )

    # Device segments
    devices = ga.query(
        ["deviceCategory"],
        ["sessions", "totalUsers", "engagedSessions", "engagementRate",
         "bounceRate", "averageSessionDuration"],
        days=days, limit=5, order="sessions"
    )

    # Calculate segment quality
    for seg in new_ret:
        if "_error" not in seg:
            eng = safe_float(seg.get("engagementRate", 0))
            pps = safe_float(seg.get("screenPageViewsPerSession", 0))
            dur = safe_float(seg.get("averageSessionDuration", 0))
            seg["quality"] = eng * 0.4 + min(pps/5, 1) * 0.3 + min(dur/300, 1) * 0.3

    return {
        "new_vs_returning": new_ret,
        "by_channel": session_count,
        "by_device": devices
    }


def analyze_time_patterns(ga: GA4, days: int) -> Dict:
    """Time patterns - when do users engage."""

    # Hourly
    hourly = ga.query(
        ["hour"],
        ["sessions", "totalUsers", "engagementRate"],
        days=days, limit=24
    )
    hourly = sorted([h for h in hourly if "_error" not in h],
                   key=lambda x: int(x.get("hour", 0)))

    # Daily
    daily_dow = ga.query(
        ["dayOfWeek"],
        ["sessions", "totalUsers", "engagementRate", "averageSessionDuration"],
        days=days, limit=7
    )
    daily_dow = sorted([d for d in daily_dow if "_error" not in d],
                      key=lambda x: int(x.get("dayOfWeek", 0)))

    # Trend over period
    trend = ga.query(
        ["date"],
        ["sessions", "totalUsers", "newUsers", "engagedSessions", "screenPageViews"],
        days=days, limit=days+1
    )
    trend = sorted([t for t in trend if "_error" not in t], key=lambda x: x.get("date", ""))

    # Calculate 7-day rolling average
    if len(trend) >= 7:
        for i in range(6, len(trend)):
            window = trend[i-6:i+1]
            avg = sum(safe_int(t["sessions"]) for t in window) / 7
            trend[i]["rolling_avg"] = avg

    return {
        "hourly": hourly,
        "daily": daily_dow,
        "trend": trend
    }


def analyze_technology(ga: GA4, days: int) -> Dict:
    """Technology breakdown."""

    # Devices
    devices = ga.query(
        ["deviceCategory"],
        ["sessions", "totalUsers", "engagementRate", "bounceRate"],
        days=days, limit=5, order="sessions"
    )

    # Browsers
    browsers = ga.query(
        ["browser"],
        ["sessions", "totalUsers", "engagementRate", "bounceRate"],
        days=days, limit=12, order="sessions"
    )

    # OS
    os_data = ga.query(
        ["operatingSystem"],
        ["sessions", "totalUsers", "engagementRate"],
        days=days, limit=10, order="sessions"
    )

    # Screen resolutions
    screens = ga.query(
        ["screenResolution"],
        ["sessions", "totalUsers"],
        days=days, limit=15, order="sessions"
    )

    return {
        "devices": devices,
        "browsers": browsers,
        "os": os_data,
        "screens": screens
    }


def calculate_health_scores(data: Dict, days: int) -> Dict:
    """Calculate comprehensive health scores."""

    scores = {}
    exec_data = data.get("executive", {})
    current = exec_data.get("current", {})
    previous = exec_data.get("previous", {})
    activity = exec_data.get("activity", {})

    # 1. ENGAGEMENT (0-100)
    eng_rate = safe_float(current.get("engagementRate", 0))
    duration = safe_float(current.get("averageSessionDuration", 0))
    pps = safe_float(current.get("screenPageViewsPerSession", 0))
    scores["engagement"] = min(100, int(eng_rate * 50 + min(duration/180, 1) * 25 + min(pps/4, 1) * 25))

    # 2. TRAFFIC DIVERSITY (0-100)
    channels = data.get("acquisition", {}).get("channels", [])
    if channels:
        total = sum(safe_int(c.get("sessions", 0)) for c in channels if "_error" not in c)
        top = safe_int(channels[0].get("sessions", 0)) if channels else 0
        scores["traffic_diversity"] = int((1 - top/total) * 100) if total > 0 else 50
    else:
        scores["traffic_diversity"] = 50

    # 3. RETENTION (0-100)
    dau = safe_int(activity.get("active1DayUsers", 0))
    wau = safe_int(activity.get("active7DayUsers", 0))
    mau = safe_int(activity.get("active28DayUsers", 0))
    dau_mau = dau / mau if mau > 0 else 0
    scores["retention"] = min(100, int(dau_mau * 500))  # 20% = 100

    # 4. GROWTH (0-100)
    curr_sess = safe_int(current.get("sessions", 0))
    prev_sess = safe_int(previous.get("sessions", 0))
    if prev_sess > 0:
        growth = (curr_sess - prev_sess) / prev_sess
        scores["growth"] = min(100, max(0, int(50 + growth * 100)))
    else:
        scores["growth"] = 75 if curr_sess > 0 else 50

    # 5. CONTENT QUALITY (0-100)
    high_bounce = data.get("content", {}).get("high_bounce", [])
    total_pages = len(data.get("content", {}).get("pages", []))
    bounce_ratio = len(high_bounce) / max(total_pages, 1)
    scores["content"] = max(0, int(100 - bounce_ratio * 300))

    # 6. MOBILE (0-100)
    devices = data.get("technology", {}).get("devices", [])
    if devices:
        total = sum(safe_int(d.get("sessions", 0)) for d in devices if "_error" not in d)
        mobile = sum(safe_int(d.get("sessions", 0)) for d in devices
                    if "_error" not in d and d.get("deviceCategory") in ["mobile", "tablet"])
        mobile_pct = mobile / total if total > 0 else 0
        # Ideal is 30-60%
        if 0.3 <= mobile_pct <= 0.6:
            scores["mobile"] = 95
        elif mobile_pct > 0.15:
            scores["mobile"] = 75
        else:
            scores["mobile"] = 45
    else:
        scores["mobile"] = 50

    # 7. GEO DIVERSITY (0-100)
    countries = data.get("geography", {}).get("countries", [])
    if countries:
        total = sum(safe_int(c.get("sessions", 0)) for c in countries if "_error" not in c)
        top_country = safe_int(countries[0].get("sessions", 0)) if countries else 0
        scores["geo_diversity"] = int((1 - top_country/total) * 100) if total > 0 else 50
    else:
        scores["geo_diversity"] = 50

    return scores
