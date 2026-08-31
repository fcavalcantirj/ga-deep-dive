"""Shared chart-test data and helpers, split out of test_charts.py so neither
half of the suite crosses the golden-rules file-size ceiling."""

import json

import matplotlib.pyplot as plt
from matplotlib import gridspec

FULL_DATA = {
    "property": "repo-atlas",
    "days": 7,
    "generated_at": "2026-08-31 12:00 UTC",
    "realtime": {"active_users": 12},
    "executive": {
        "current": {
            "sessions": 1570, "activeUsers": 960, "newUsers": 300, "engagedSessions": 800,
            "engagementRate": 0.512, "bounceRate": 0.30, "averageSessionDuration": 145.0,
            "screenPageViewsPerSession": 2.4, "screenPageViews": 3770,
        },
        "previous": {
            "sessions": 980, "activeUsers": 700, "newUsers": 250, "engagedSessions": 600,
            "engagementRate": 0.40, "bounceRate": 0.50, "averageSessionDuration": 120.0,
            "screenPageViewsPerSession": 2.0, "screenPageViews": 2500,
        },
    },
    "activity": {
        "active1DayUsers": 120, "active7DayUsers": 500, "active28DayUsers": 1800,
        "dauPerWau": 0.24, "dauPerMau": 0.067,
    },
    "health": {
        "scores": {
            "Growth": 82,
            "Content": 55,
            "Engagement": 51,
            "Mobile": 38,
            "Geo Diversity": 70,
            "Retention": None,
            "Traffic Diversity": 90,
        },
        "overall": 64,
        "grade": "B",
    },
    "acquisition": {
        "channels": [
            {"name": "Organic Search", "sessions": 600},
            {"name": "Direct", "sessions": 400},
            {"name": "Referral", "sessions": 250},
            {"name": "Social", "sessions": 150},
            {"name": "Email", "sessions": 90},
            {"name": "Paid Search", "sessions": 50},
            {"name": "Display", "sessions": 20},
            {"name": "Other", "sessions": 10},
        ],
        "top_referrer": {"source_medium": "news.ycombinator.com / referral", "sessions": 210},
        "first_touch": [
            {"source": "google", "medium": "organic", "sessions": 600, "share": 0.38},
            {"source": "(direct)", "medium": "(none)", "sessions": 400, "share": 0.25},
            {"source": "news.ycombinator.com", "medium": "referral", "sessions": 210, "share": 0.13},
        ],
    },
    "geography": {
        "countries": [
            {"name": "United States", "sessions": 700},
            {"name": "Brazil", "sessions": 300},
            {"name": "Germany", "sessions": 200},
            {"name": "India", "sessions": 150},
            {"name": "United Kingdom", "sessions": 100},
            {"name": "Canada", "sessions": 60},
            {"name": "France", "sessions": 40},
            {"name": "Japan", "sessions": 20},
        ],
        "languages": [
            {"name": "en-us", "sessions": 900, "share": 0.57},
            {"name": "pt-br", "sessions": 300, "share": 0.19},
            {"name": "de-de", "sessions": 200, "share": 0.13},
        ],
    },
    "content": {
        "sections": [
            {"section": "/docs", "views": 2200, "engagement_pct": 0.61},
            {"section": "/blog", "views": 900, "engagement_pct": 0.44},
            {"section": "/pricing", "views": 500, "engagement_pct": 0.30},
        ],
        "trending_up": [
            {"path": "/docs/quickstart", "pct_change": 0.85},
            {"path": "/blog/launch", "pct_change": 0.42},
        ],
        "problem_pages": [
            {"path": "/promo/expired-campaign", "bounce_pct": 1.0},
            {"path": "/legacy/signup", "bounce_pct": 0.72},
        ],
    },
    "segments": {
        "new_vs_returning": [
            {"segment": "New", "sessions": 900, "engagement_pct": 0.48},
            {"segment": "Returning", "sessions": 670, "engagement_pct": 0.58},
        ],
        "by_device": [
            {"device": "mobile", "sessions": 900, "share": 0.57, "engagement_pct": 0.46},
            {"device": "desktop", "sessions": 600, "share": 0.38, "engagement_pct": 0.55},
            {"device": "tablet", "sessions": 70, "share": 0.05, "engagement_pct": 0.40},
        ],
    },
    "time_patterns": {
        "day_of_week": [
            {"day_name": "Monday", "sessions": 300, "engaged_pct": 0.5},
            {"day_name": "Tuesday", "sessions": 260, "engaged_pct": 0.48},
            {"day_name": "Wednesday", "sessions": 280, "engaged_pct": 0.52},
        ],
    },
    "technology": {
        "browsers": [
            {"name": "Chrome", "sessions": 1100, "engaged_pct": 0.55},
            {"name": "Safari", "sessions": 350, "engaged_pct": 0.49},
            {"name": "Firefox", "sessions": 120, "engaged_pct": 0.51},
        ],
        "resolutions": [
            {"resolution": "1920x1080", "sessions": 500},
            {"resolution": "390x844", "sessions": 420},
            {"resolution": "1366x768", "sessions": 200},
        ],
    },
    "acquisition_over_time": {
        "daily": [
            {"date": "08-25", "users": 100},
            {"date": "08-26", "users": 140},
            {"date": "08-27", "users": 90},
            {"date": "08-28", "users": 200},
            {"date": "08-29", "users": 160},
            {"date": "08-30", "users": 180},
            {"date": "08-31", "users": 220},
        ]
    },
    "hourly_performance": {
        "hours": [{"hour": h, "sessions": (h * 7) % 53 + 5, "engagement_rate": 0.3 + (h % 5) * 0.05} for h in range(24)],
        "best_hour": 14,
    },
    "events": {
        "events": [
            {"name": "page_view", "count": 5000},
            {"name": "example_click", "count": 1200},
            {"name": "wizard_submit", "count": 400},
            {"name": "wizard_results", "count": 250},
        ]
    },
    "gsc": {
        "available": True,
        "striking_distance": [
            {"query": "how to deploy a repo to production", "impressions": 4000, "position": 9.2},
            {"query": "ga4 deep dive skill setup guide", "impressions": 3000, "position": 12.1},
            {"query": "repo atlas onboarding checklist", "impressions": 1500, "position": 15.4},
        ],
    },
    "insights": [
        {"icon": "🟢", "message": "Sessions up 60% WoW", "action": "Double down on Organic Search"},
        {"icon": "🚨", "message": "/promo/expired-campaign has a 100% bounce rate", "action": "Fix landing page"},
        {"icon": "🔴", "message": "Low stickiness: DAU/MAU is only 6.0%", "action": "Run retention campaigns"},
    ],
}

GOAL = {"target": 1000000, "date": "2026-11-27", "metric": "totalUsers", "label": "1,000,000 users"}

BASE_EXEC_METRICS = {
    "sessions": 1000, "activeUsers": 500, "newUsers": 200, "engagedSessions": 400,
    "engagementRate": 0.5, "bounceRate": 0.4, "averageSessionDuration": 100.0,
    "screenPageViewsPerSession": 2.0, "screenPageViews": 2000,
}


def _sample_data():
    return json.loads(json.dumps(FULL_DATA))


def _png_dimensions(path):
    """Read width/height straight out of the PNG IHDR chunk — avoids pulling
    in Pillow just for a test assertion."""
    with open(path, "rb") as handle:
        header = handle.read(24)
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    return width, height


def _panel_fig():
    fig = plt.figure()
    gs = gridspec.GridSpec(1, 1, figure=fig)
    return fig, gs[0]


def _all_texts(fig):
    """All rendered text on a figure: floating `ax.text`/annotate calls, tick
    labels (bar-list panels label bars via `set_yticklabels`), and text on
    inset axes (mini-tables), which matplotlib parents under their host axes
    rather than registering directly on the figure."""
    result = []

    def _collect(ax):
        result.extend(t.get_text() for t in ax.texts)
        result.extend(t.get_text() for t in ax.get_yticklabels())
        result.extend(t.get_text() for t in ax.get_xticklabels())
        for child in getattr(ax, "child_axes", []):
            _collect(child)

    for ax in fig.axes:
        _collect(ax)
    return result


def _tile_delta(fig, label_upper):
    """Find the delta text for the tile whose label matches `label_upper`
    (tiles draw value/label/delta as texts[0]/[1]/[2] on their own axis)."""
    for ax in fig.axes:
        texts = ax.texts
        if len(texts) >= 2 and texts[1].get_text() == label_upper:
            return texts[2] if len(texts) >= 3 else None
    return None
