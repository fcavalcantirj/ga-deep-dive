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


def northstar_totals(backend: Backend, metric: str = "totalUsers") -> Dict[str, float]:
    """North-star pacing inputs: the goal metric's all-time cumulative total
    plus a 28-day daily rate.

    `current_total` is a single-row report pinned to an explicit lifetime
    dateRange (2020-01-01 .. today) — GA4 has no running-total metric, so a
    wide-enough fixed start date stands in for "since we started tracking".
    `current_rate` is newUsers over the last complete 28 days (28daysAgo ..
    yesterday), averaged per day.
    """
    total_rows = backend.run_report(
        [],
        [metric],
        1,
        extra={"row_key": "northstar_total", "date_ranges": [{"startDate": "2020-01-01", "endDate": "today"}]},
    )
    current_total = float(total_rows[0].get(metric, 0)) if total_rows else 0.0

    rate_rows = backend.run_report(
        [],
        ["newUsers"],
        28,
        extra={"row_key": "northstar_rate", "date_ranges": [{"startDate": "28daysAgo", "endDate": "yesterday"}]},
    )
    new_users_28d = float(rate_rows[0].get("newUsers", 0)) if rate_rows else 0.0

    return {"current_total": current_total, "current_rate": new_users_28d / 28}


def user_activity(backend: Backend) -> Dict[str, Any]:
    """§3 User Activity — DAU/WAU/MAU + stickiness, as a POINT-IN-TIME
    snapshot for the last complete day.

    GA4's rolling active-user metrics (active1DayUsers/7Day/28Day) are
    per-date metrics: querying them over a multi-day range with no `date`
    dimension makes GA4 SUM each day's value across the range, which is what
    produced DAU/WAU and DAU/MAU readings above 100% in R1. The fix is a
    single-row query pinned to exactly one day (yesterday, the last complete
    day) — never a range, never a date-dimension sum. Stickiness is read
    directly off the dauPerWau/dauPerMau metrics GA4 computes server-side,
    never derived by dividing DAU/WAU or DAU/MAU ourselves.
    """
    rows = backend.run_report(
        [], ACTIVITY_METRICS, 1, extra={"date_ranges": [{"startDate": "yesterday", "endDate": "yesterday"}]}
    )
    return dict(rows[0]) if rows else {}
