"""Pure section fetchers for PART 1 §1-4: realtime, executive summary, user
activity. Each function takes a `Backend` and returns a plain dict — no
formatting, no printing.
"""

from typing import Any, Dict

from .backends.base import Backend

REALTIME_METRICS = ["activeUsers"]

EXECUTIVE_METRICS = [
    "sessions",
    "activeUsers",
    "newUsers",
    "engagedSessions",
    "engagementRate",
    "bounceRate",
    "averageSessionDuration",
    "screenPageViewsPerSession",
    "screenPageViews",
]

ACTIVITY_METRICS = [
    "active1DayUsers",
    "active7DayUsers",
    "active28DayUsers",
    "dauPerWau",
    "dauPerMau",
]


def realtime_active_users(backend: Backend) -> Dict[str, int]:
    """§2 LIVE NOW — current realtime active users."""
    rows = backend.run_realtime(REALTIME_METRICS)
    active_users = int(rows[0]["activeUsers"]) if rows else 0
    return {"active_users": active_users}


def executive_summary(backend: Backend, days: int) -> Dict[str, Dict[str, Any]]:
    """§3 EXECUTIVE SUMMARY — current vs previous period (WoW)."""
    rows = backend.run_report([], EXECUTIVE_METRICS, days, extra={"compare_previous": True})

    current = next((row for row in rows if row.get("dateRange") == "current"), {})
    previous = next((row for row in rows if row.get("dateRange") == "previous"), {})

    return {
        "current": {k: v for k, v in current.items() if k != "dateRange"},
        "previous": {k: v for k, v in previous.items() if k != "dateRange"},
    }


def user_activity(backend: Backend, days: int) -> Dict[str, Any]:
    """§3 User Activity — DAU/WAU/MAU + stickiness ratios."""
    rows = backend.run_report([], ACTIVITY_METRICS, days)
    return dict(rows[0]) if rows else {}
