"""Small pure helpers shared by the §5-12 `fetch_*.py` modules — ratio/share
math and GA4 `orderBys` construction. No backend calls, no formatting.
"""

from typing import Any, Dict, List, Optional


def safe_ratio(numerator: Optional[float], denominator: Optional[float]) -> float:
    numerator = float(numerator or 0)
    denominator = float(denominator or 0)
    return (numerator / denominator) if denominator else 0.0


def share_of_total(value: Optional[float], total: float) -> float:
    return safe_ratio(value, total)


def total_of(rows: List[Dict[str, Any]], key: str) -> float:
    return sum(float(row.get(key, 0) or 0) for row in rows)


def order_by_metric(metric_name: str, desc: bool = True) -> List[Dict[str, Any]]:
    return [{"metric": {"metricName": metric_name}, "desc": desc}]


def blank_label(value: Optional[str], fallback: str = "(not set)") -> str:
    """Render a readable label for a GA4/GSC dimension value that may be
    `None` or an empty string (both are distinct from the literal `"(not
    set)"` GA4 sometimes sends, which passes through unchanged)."""
    return value if value else fallback
