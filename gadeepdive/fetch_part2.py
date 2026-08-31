"""Pure section fetchers for PART 2 §13-18: scroll depth, user flow entry
points, GA4 audiences, hourly performance, acquisition over time, and mobile
devices. Each function takes a `Backend` and returns a plain dict — no
formatting.
"""

from typing import Any, Dict

from .backends.base import Backend
from .fetch_util import blank_label, order_by_metric, safe_ratio, total_of

SCROLL_BUCKETS = ["10", "25", "50", "75", "90", "100"]
SCROLL_COMPLETION_BUCKETS = {"90", "100"}

HOURLY_METRICS = ["sessions", "engagedSessions", "engagementRate", "averageSessionDuration"]

AUDIENCE_EXCLUDED = {None, "(not set)", "All Users"}
MOBILE_MODEL_EXCLUDED = {None, "(not set)"}


def _format_ga4_date(raw: Any) -> str:
    """GA4's `date` dimension is `YYYYMMDD`; render as `MM-DD`."""
    text = str(raw)
    if len(text) == 8 and text.isdigit():
        return f"{text[4:6]}-{text[6:8]}"
    return text


def scroll_depth(backend: Backend, days: int) -> Dict[str, Any]:
    """§13 SCROLL DEPTH — overall depth-bucket distribution, plus per-page
    completion rate (share of pageviews reaching 90%+ scroll)."""
    dist_rows = backend.run_report(["percentScrolled"], ["eventCount"], days, extra={"row_key": "scroll_distribution"})
    total_events = total_of(dist_rows, "eventCount")
    by_bucket = {str(row.get("percentScrolled")): row.get("eventCount", 0) for row in dist_rows}
    distribution = [
        {"depth": bucket, "count": by_bucket.get(bucket, 0), "share": safe_ratio(by_bucket.get(bucket, 0), total_events)}
        for bucket in SCROLL_BUCKETS
    ]

    page_rows = backend.run_report(
        ["pagePath", "percentScrolled"],
        ["eventCount", "screenPageViews"],
        days,
        extra={"row_key": "scroll_by_page"},
    )
    pageviews: Dict[str, float] = {}
    deep_scroll: Dict[str, float] = {}
    for row in page_rows:
        path = blank_label(row.get("pagePath"), "(direct entry)")
        views = float(row.get("screenPageViews", 0) or 0)
        pageviews[path] = max(pageviews.get(path, 0.0), views)
        if str(row.get("percentScrolled")) in SCROLL_COMPLETION_BUCKETS:
            deep_scroll[path] = deep_scroll.get(path, 0.0) + float(row.get("eventCount", 0) or 0)

    top_pages = [{"path": path, "completion_rate": safe_ratio(deep_scroll.get(path, 0.0), views)} for path, views in pageviews.items()]
    top_pages.sort(key=lambda p: p["completion_rate"], reverse=True)

    return {"distribution": distribution, "total_events": total_events, "top_pages": top_pages}


def user_flow(backend: Backend, days: int) -> Dict[str, Any]:
    """§14 USER FLOW — ENTRY POINTS — landing page entries (sessions) and bounce%."""
    rows = backend.run_report(
        ["landingPagePlusQueryString"],
        ["sessions", "bounceRate"],
        days,
        extra={"row_key": "flow_entries", "order_bys": order_by_metric("sessions")},
    )
    entries = [
        {
            "path": blank_label(row.get("landingPagePlusQueryString"), "(direct entry)"),
            "entries": row.get("sessions", 0),
            "bounce_pct": float(row.get("bounceRate", 0) or 0),
        }
        for row in sorted(rows, key=lambda r: float(r.get("sessions", 0) or 0), reverse=True)
    ]
    return {"entries": entries}


def audiences(backend: Backend, days: int) -> Dict[str, Any]:
    """§15 GA4 AUDIENCES — audience users/sessions/engagement rate."""
    rows = backend.run_report(
        ["audienceName"],
        ["activeUsers", "sessions", "engagementRate"],
        days,
        extra={"row_key": "audiences", "order_bys": order_by_metric("activeUsers")},
    )
    audience_list = [
        {
            "name": row.get("audienceName"),
            "users": row.get("activeUsers", 0),
            "sessions": row.get("sessions", 0),
            "engagement_pct": float(row.get("engagementRate", 0) or 0),
        }
        for row in rows
        if row.get("audienceName") not in AUDIENCE_EXCLUDED
    ]
    audience_list.sort(key=lambda a: float(a["users"] or 0), reverse=True)
    return {"audiences": audience_list}


def hourly_performance(backend: Backend, days: int) -> Dict[str, Any]:
    """§16 HOURLY PERFORMANCE — sessions/engagement by hour, peak hour flagged."""
    rows = backend.run_report(["hour"], HOURLY_METRICS, days, extra={"row_key": "hourly"})
    hours = [
        {
            "hour": int(row.get("hour", 0) or 0),
            "sessions": row.get("sessions", 0),
            "engaged": row.get("engagedSessions", 0),
            "engagement_rate": float(row.get("engagementRate", 0) or 0),
            "avg_duration": float(row.get("averageSessionDuration", 0) or 0),
        }
        for row in rows
    ]
    hours.sort(key=lambda h: h["hour"])
    best_hour = max(hours, key=lambda h: h["engagement_rate"])["hour"] if hours else None
    return {"hours": hours, "best_hour": best_hour}


def acquisition_over_time(backend: Backend, days: int) -> Dict[str, Any]:
    """§17 ACQUISITION OVER TIME — daily active users, sorted desc by users."""
    rows = backend.run_report(["date"], ["activeUsers"], days, extra={"row_key": "acq_over_time"})
    daily = [{"date": _format_ga4_date(row.get("date")), "users": row.get("activeUsers", 0)} for row in rows]
    daily.sort(key=lambda d: float(d["users"] or 0), reverse=True)
    return {"daily": daily}


def mobile_devices(backend: Backend, days: int) -> Dict[str, Any]:
    """§18 MOBILE DEVICES — sessions by mobile device model."""
    rows = backend.run_report(
        ["mobileDeviceModel"], ["sessions"], days, extra={"row_key": "mobile_devices", "order_bys": order_by_metric("sessions")}
    )
    models = [
        {"model": blank_label(row.get("mobileDeviceModel"), "(unknown device)"), "sessions": row.get("sessions", 0)}
        for row in rows
        if row.get("mobileDeviceModel") not in MOBILE_MODEL_EXCLUDED
    ]
    models.sort(key=lambda m: float(m["sessions"] or 0), reverse=True)
    return {"models": models}
