"""Pure section fetcher for PART 1 §7 CONTENT: pages grouped into sections,
week-over-week trending pages, and problem (high-bounce landing) pages.
"""

from typing import Any, Dict, List

from .backends.base import Backend
from .fetch_util import blank_label, order_by_metric

PAGE_METRICS = ["screenPageViews", "activeUsers", "engagementRate"]
LANDING_METRICS = ["sessions", "bounceRate"]

PROBLEM_PAGE_BOUNCE_THRESHOLD = 0.95


def _section_for_path(path: str) -> str:
    """First path segment of a pagePath, e.g. `/docs/api/auth` -> `docs`."""
    parts = [p for p in str(path or "/").split("/") if p]
    return parts[0] if parts else "(root)"


def _group_by_section(page_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in page_rows:
        section = _section_for_path(row.get("pagePath"))
        views = float(row.get("screenPageViews", 0) or 0)
        users = float(row.get("activeUsers", 0) or 0)
        engagement_rate = float(row.get("engagementRate", 0) or 0)

        bucket = grouped.setdefault(
            section, {"section": section, "views": 0.0, "users": 0.0, "page_count": 0, "_weighted_engagement": 0.0}
        )
        bucket["views"] += views
        bucket["users"] += users
        bucket["page_count"] += 1
        bucket["_weighted_engagement"] += engagement_rate * views

    sections = []
    for bucket in grouped.values():
        engagement_pct = (bucket["_weighted_engagement"] / bucket["views"]) if bucket["views"] else 0.0
        sections.append(
            {
                "section": bucket["section"],
                "views": bucket["views"],
                "users": bucket["users"],
                "page_count": bucket["page_count"],
                "engagement_pct": engagement_pct,
            }
        )
    sections.sort(key=lambda s: s["views"], reverse=True)
    return sections


def _wow_trending(compare_rows: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """Top % gainers by pagePath, from a single current-vs-previous query."""
    current: Dict[str, float] = {}
    previous: Dict[str, float] = {}
    for row in compare_rows:
        path = row.get("pagePath")
        views = float(row.get("screenPageViews", 0) or 0)
        if row.get("dateRange") == "current":
            current[path] = views
        elif row.get("dateRange") == "previous":
            previous[path] = views

    gainers = []
    for path, current_views in current.items():
        previous_views = previous.get(path, 0.0)
        if previous_views <= 0:
            continue  # no baseline to compute a % change against
        pct_change = (current_views - previous_views) / previous_views
        if pct_change > 0:
            gainers.append({"path": path, "current_views": current_views, "previous_views": previous_views, "pct_change": pct_change})

    gainers.sort(key=lambda g: g["pct_change"], reverse=True)
    return gainers[:top_n]


def _problem_pages(landing_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    problems = [
        {
            "path": blank_label(row.get("landingPage"), "(direct entry)"),
            "sessions": row.get("sessions", 0),
            "bounce_pct": float(row.get("bounceRate", 0) or 0),
        }
        for row in landing_rows
        if float(row.get("bounceRate", 0) or 0) >= PROBLEM_PAGE_BOUNCE_THRESHOLD
    ]
    problems.sort(key=lambda p: p["bounce_pct"], reverse=True)
    return problems


def content(backend: Backend, days: int) -> Dict[str, Any]:
    """§7 CONTENT — page sections, WoW trending pages, problem pages."""
    page_rows = backend.run_report(
        ["pagePath"], PAGE_METRICS, days, extra={"row_key": "content_pages", "order_bys": order_by_metric("screenPageViews")}
    )
    sections = _group_by_section(page_rows)

    compare_rows = backend.run_report(
        ["pagePath"],
        ["screenPageViews"],
        days,
        extra={"compare_previous": True, "row_key": "content_trending"},
    )
    trending_up = _wow_trending(compare_rows)

    landing_rows = backend.run_report(
        ["landingPage"], LANDING_METRICS, days, extra={"row_key": "content_landing", "order_bys": order_by_metric("sessions")}
    )
    problem_pages = _problem_pages(landing_rows)

    return {"sections": sections, "trending_up": trending_up, "problem_pages": problem_pages}
