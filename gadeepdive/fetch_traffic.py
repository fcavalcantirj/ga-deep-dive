"""Pure section fetchers for PART 1 §5 ACQUISITION and §6 GEOGRAPHY. Each
function takes a `Backend` and returns a plain dict — no formatting.
"""

from typing import Any, Dict

from .backends.base import Backend
from .fetch_util import order_by_metric, safe_ratio, share_of_total, total_of

CHANNEL_METRICS = ["sessions", "engagedSessions", "bounceRate", "averageSessionDuration"]
COUNTRY_METRICS = ["sessions", "engagedSessions", "engagementRate"]

_STAR_THRESHOLDS = [(0.6, 5), (0.45, 4), (0.3, 3), (0.15, 2)]


def _stars_for_engagement_rate(rate: float) -> int:
    """Map GA4 `engagementRate` (0-1 fraction) to a 1-5 quality-star rating."""
    rate = float(rate or 0)
    for threshold, stars in _STAR_THRESHOLDS:
        if rate >= threshold:
            return stars
    return 1


def acquisition(backend: Backend, days: int) -> Dict[str, Any]:
    """§5 ACQUISITION — channel breakdown, top referrer, first-touch attribution."""
    channel_rows = backend.run_report(
        ["sessionDefaultChannelGroup"],
        CHANNEL_METRICS,
        days,
        extra={"row_key": "acq_channels", "order_bys": order_by_metric("sessions")},
    )
    total_sessions = total_of(channel_rows, "sessions")
    channels = [
        {
            "name": row.get("sessionDefaultChannelGroup", "(not set)"),
            "sessions": row.get("sessions", 0),
            "share": share_of_total(row.get("sessions"), total_sessions),
            "engaged_pct": safe_ratio(row.get("engagedSessions"), row.get("sessions")),
            "bounce_pct": float(row.get("bounceRate", 0) or 0),
            "avg_duration": float(row.get("averageSessionDuration", 0) or 0),
        }
        for row in sorted(channel_rows, key=lambda r: float(r.get("sessions", 0) or 0), reverse=True)
    ]

    source_medium_rows = backend.run_report(
        ["sessionSourceMedium"],
        ["sessions"],
        days,
        extra={"row_key": "acq_source_medium", "order_bys": order_by_metric("sessions")},
    )
    referrals = [row for row in source_medium_rows if "referral" in str(row.get("sessionSourceMedium", "")).lower()]
    top_referrer = None
    if referrals:
        top = max(referrals, key=lambda row: float(row.get("sessions", 0) or 0))
        top_referrer = {"source_medium": top["sessionSourceMedium"], "sessions": top.get("sessions", 0)}

    first_touch_rows = backend.run_report(
        ["firstUserSourceMedium"],
        ["sessions"],
        days,
        extra={"row_key": "acq_first_touch", "order_bys": order_by_metric("sessions")},
    )
    ft_total = total_of(first_touch_rows, "sessions")
    first_touch = []
    for row in first_touch_rows:
        raw = row.get("firstUserSourceMedium", "(not set) / (not set)")
        source, _, medium = str(raw).partition(" / ")
        sessions = row.get("sessions", 0)
        first_touch.append(
            {
                "source": source or "(not set)",
                "medium": medium or "(not set)",
                "sessions": sessions,
                "share": share_of_total(sessions, ft_total),
            }
        )
    first_touch.sort(key=lambda row: float(row.get("sessions", 0) or 0), reverse=True)

    return {"channels": channels, "top_referrer": top_referrer, "first_touch": first_touch}


def geography(backend: Backend, days: int) -> Dict[str, Any]:
    """§6 GEOGRAPHY — country breakdown with quality stars, and languages."""
    country_rows = backend.run_report(
        ["country"],
        COUNTRY_METRICS,
        days,
        extra={"row_key": "geo_country", "order_bys": order_by_metric("sessions")},
    )
    total_sessions = total_of(country_rows, "sessions")
    countries = [
        {
            "name": row.get("country", "(not set)"),
            "sessions": row.get("sessions", 0),
            "share": share_of_total(row.get("sessions"), total_sessions),
            "engaged_pct": safe_ratio(row.get("engagedSessions"), row.get("sessions")),
            "engagement_rate": float(row.get("engagementRate", 0) or 0),
            "stars": _stars_for_engagement_rate(row.get("engagementRate", 0)),
        }
        for row in sorted(country_rows, key=lambda r: float(r.get("sessions", 0) or 0), reverse=True)
    ]

    language_rows = backend.run_report(
        ["language"],
        ["sessions"],
        days,
        extra={"row_key": "geo_language", "order_bys": order_by_metric("sessions")},
    )
    lang_total = total_of(language_rows, "sessions")
    languages = [
        {
            "name": row.get("language", "(not set)"),
            "sessions": row.get("sessions", 0),
            "share": share_of_total(row.get("sessions"), lang_total),
        }
        for row in sorted(language_rows, key=lambda r: float(r.get("sessions", 0) or 0), reverse=True)
    ]

    return {"countries": countries, "languages": languages}
