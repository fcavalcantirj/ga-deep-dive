"""Pure section fetcher for PART 1 §8 USER SEGMENTS: new vs returning, and
the by-device breakdown (also feeds the §Part C Mobile health score).
"""

from typing import Any, Dict

from .backends.base import Backend
from .fetch_util import blank_label, order_by_metric, share_of_total, total_of


def user_segments(backend: Backend, days: int) -> Dict[str, Any]:
    """§8 USER SEGMENTS — newVsReturning table and by-device share."""
    nvr_rows = backend.run_report(
        ["newVsReturning"],
        ["sessions", "engagementRate"],
        days,
        extra={"row_key": "segments_new_returning", "order_bys": order_by_metric("sessions")},
    )
    new_vs_returning = [
        {
            "segment": blank_label(row.get("newVsReturning")),
            "sessions": row.get("sessions", 0),
            "engagement_pct": float(row.get("engagementRate", 0) or 0),
        }
        for row in nvr_rows
    ]

    device_rows = backend.run_report(
        ["deviceCategory"],
        ["sessions", "engagementRate"],
        days,
        extra={"row_key": "segments_device", "order_bys": order_by_metric("sessions")},
    )
    total_sessions = total_of(device_rows, "sessions")
    by_device = [
        {
            "device": blank_label(row.get("deviceCategory")),
            "sessions": row.get("sessions", 0),
            "share": share_of_total(row.get("sessions"), total_sessions),
            "engagement_pct": float(row.get("engagementRate", 0) or 0),
        }
        for row in sorted(device_rows, key=lambda r: float(r.get("sessions", 0) or 0), reverse=True)
    ]

    return {"new_vs_returning": new_vs_returning, "by_device": by_device}
