"""North-star pacing math — pure functions over an optional per-property
"goal" (registry.py) and the already-fetched executive summary.

No GA4 call of its own: there is no persisted lifetime counter to query, so
"current total" reads off the current-period value of the goal's metric in
`data["executive"]` — the only running total this app already has.
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
    executive = data.get("executive") or {}
    current_total = float((executive.get("current") or {}).get(metric, 0) or 0)
    previous_total = float((executive.get("previous") or {}).get(metric, 0) or 0)
    period_days = int(data.get("days") or 1) or 1

    generated_at = str(data.get("generated_at", ""))
    today = _parse_date(generated_at[:10]) if generated_at[:10] else date.today()
    target_date = _parse_date(goal["date"])
    days_left = max((target_date - today).days, 0)

    percent = (current_total / target * 100) if target else 0.0
    remaining = max(target - current_total, 0.0)
    required_rate = (remaining / days_left) if days_left else remaining
    current_rate = (current_total - previous_total) / period_days

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
