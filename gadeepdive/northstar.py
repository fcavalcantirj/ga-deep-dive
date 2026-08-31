"""North-star pacing math — pure functions over an optional per-property
"goal" (registry.py) and the already-fetched goal totals.

No GA4 call of its own: `data["goal_totals"]` (fetch.northstar_totals) is
the lifetime counter — an explicit all-time dateRange query — and the 28-day
daily rate, both fetched by cli.py before this module ever runs.
"""

from datetime import date, datetime
from typing import Any, Dict, Optional

DATE_FORMAT = "%Y-%m-%d"


def _parse_date(value: str) -> date:
    return datetime.strptime(value, DATE_FORMAT).date()


def compute_pacing(data: Dict[str, Any], goal: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the pacing summary for `goal`, or None when there is no goal."""
    if not goal:
        return None

    metric = goal["metric"]
    target = float(goal["target"])
    totals = data.get("goal_totals") or {}
    current_total = float(totals.get("current_total", 0) or 0)
    current_rate = float(totals.get("current_rate", 0) or 0)

    generated_at = str(data.get("generated_at", ""))
    today = _parse_date(generated_at[:10]) if generated_at[:10] else date.today()
    target_date = _parse_date(goal["date"])
    days_left = max((target_date - today).days, 0)

    percent = (current_total / target * 100) if target else 0.0
    remaining = max(target - current_total, 0.0)
    required_rate = (remaining / days_left) if days_left else remaining

    return {
        "label": goal.get("label") or metric,
        "metric": metric,
        "target": target,
        "current_total": current_total,
        "percent": percent,
        "days_left": days_left,
        "current_rate": current_rate,
        "required_rate": required_rate,
        "ahead": current_rate >= required_rate,
    }
