"""Pure section fetcher for PART 1 §11 TECHNOLOGY: browsers and top screen
resolutions.
"""

from typing import Any, Dict

from .backends.base import Backend
from .fetch_util import order_by_metric, safe_ratio


def technology(backend: Backend, days: int) -> Dict[str, Any]:
    """§11 TECHNOLOGY — browser breakdown and top screen resolutions."""
    browser_rows = backend.run_report(
        ["browser"],
        ["sessions", "engagedSessions"],
        days,
        extra={"row_key": "tech_browser", "order_bys": order_by_metric("sessions")},
    )
    browsers = [
        {
            "name": row.get("browser", "(not set)"),
            "sessions": row.get("sessions", 0),
            "engaged_pct": safe_ratio(row.get("engagedSessions"), row.get("sessions")),
        }
        for row in sorted(browser_rows, key=lambda r: float(r.get("sessions", 0) or 0), reverse=True)
    ]

    resolution_rows = backend.run_report(
        ["screenResolution"],
        ["sessions"],
        days,
        extra={"row_key": "tech_resolution", "order_bys": order_by_metric("sessions")},
    )
    resolutions = [
        {"resolution": row.get("screenResolution", "(not set)"), "sessions": row.get("sessions", 0)}
        for row in sorted(resolution_rows, key=lambda r: float(r.get("sessions", 0) or 0), reverse=True)
    ]

    return {"browsers": browsers, "resolutions": resolutions}
