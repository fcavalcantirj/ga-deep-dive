"""Pure section fetchers for PART 1 §9 EVENTS and §10 TIME PATTERNS."""

from typing import Any, Dict

from .backends.base import Backend
from .fetch_util import order_by_metric, safe_ratio

_WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

LAST_7_DAYS = 7


def _weekday_name(code: Any) -> str:
    """GA4's `dayOfWeek` dimension is `"0"`-`"6"` with 0 = Sunday."""
    try:
        return _WEEKDAY_NAMES[int(code)]
    except (TypeError, ValueError, IndexError):
        return str(code)


def _format_ga4_date(raw: Any) -> str:
    """GA4's `date` dimension is `YYYYMMDD`; render as `MM-DD`."""
    text = str(raw)
    if len(text) == 8 and text.isdigit():
        return f"{text[4:6]}-{text[6:8]}"
    return text


def events(backend: Backend, days: int) -> Dict[str, Any]:
    """§9 EVENTS — event name, count, per-user rate."""
    rows = backend.run_report(
        ["eventName"],
        ["eventCount", "eventCountPerUser"],
        days,
        extra={"row_key": "events", "order_bys": order_by_metric("eventCount")},
    )
    events_list = [
        {
            "name": row.get("eventName", "(not set)"),
            "count": row.get("eventCount", 0),
            "per_user": float(row.get("eventCountPerUser", 0) or 0),
        }
        for row in sorted(rows, key=lambda r: float(r.get("eventCount", 0) or 0), reverse=True)
    ]
    return {"events": events_list}


def time_patterns(backend: Backend, days: int) -> Dict[str, Any]:
    """§10 TIME PATTERNS — day-of-week bars and a last-7-days sparkline."""
    dow_rows = backend.run_report(
        ["dayOfWeek"], ["sessions", "engagedSessions"], days, extra={"row_key": "time_day_of_week"}
    )
    day_of_week = []
    for row in sorted(dow_rows, key=lambda r: int(r.get("dayOfWeek", 0) or 0)):
        sessions = row.get("sessions", 0)
        day_of_week.append(
            {
                "day_name": _weekday_name(row.get("dayOfWeek")),
                "sessions": sessions,
                "engaged_pct": safe_ratio(row.get("engagedSessions"), sessions),
            }
        )

    daily_rows = backend.run_report(["date"], ["sessions"], LAST_7_DAYS, extra={"row_key": "time_daily"})
    daily = [
        {"date": _format_ga4_date(row.get("date")), "sessions": row.get("sessions", 0)}
        for row in sorted(daily_rows, key=lambda r: str(r.get("date", "")))
    ]

    return {"day_of_week": day_of_week, "daily": daily}
