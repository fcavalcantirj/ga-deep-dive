"""Pure section fetcher for the GSC (Google Search Console) add-on: totals,
top queries, and a striking-distance quick-wins list. Gracefully returns
`{"available": False}` and never calls the backend when it has no configured
`gsc_site` (properties without a registered GSC site).
"""

from typing import Any, Dict

from .backends.base import Backend
from .fetch_util import blank_label, safe_ratio, total_of

GSC_ROW_LIMIT = 100

STRIKING_DISTANCE_MIN_POSITION = 8.0
STRIKING_DISTANCE_MAX_POSITION = 20.0
STRIKING_DISTANCE_MIN_IMPRESSIONS = 5
STRIKING_DISTANCE_LIMIT = 10


def _is_striking_distance(query: Dict[str, Any]) -> bool:
    return (
        STRIKING_DISTANCE_MIN_POSITION <= query["position"] <= STRIKING_DISTANCE_MAX_POSITION
        and query["impressions"] >= STRIKING_DISTANCE_MIN_IMPRESSIONS
    )


def gsc_report(backend: Backend, days: int, row_limit: int = GSC_ROW_LIMIT) -> Dict[str, Any]:
    """GSC add-on — totals, top queries, striking-distance quick wins."""
    if not getattr(backend, "gsc_site", None):
        return {"available": False}

    rows = backend.gsc_query(["query"], days, row_limit=row_limit)
    queries = [
        {
            "query": blank_label(row.get("query")),
            "clicks": float(row.get("clicks", 0) or 0),
            "impressions": float(row.get("impressions", 0) or 0),
            "ctr": float(row.get("ctr", 0) or 0),
            "position": float(row.get("position", 0) or 0),
        }
        for row in rows
    ]

    total_clicks = total_of(queries, "clicks")
    total_impressions = total_of(queries, "impressions")
    weighted_position = sum(q["position"] * q["impressions"] for q in queries)

    totals = {
        "clicks": total_clicks,
        "impressions": total_impressions,
        "ctr": safe_ratio(total_clicks, total_impressions),
        "avg_position": safe_ratio(weighted_position, total_impressions),
    }

    top_queries = sorted(queries, key=lambda q: q["clicks"], reverse=True)
    striking_distance = sorted((q for q in queries if _is_striking_distance(q)), key=lambda q: q["impressions"], reverse=True)[
        :STRIKING_DISTANCE_LIMIT
    ]

    return {"available": True, "totals": totals, "top_queries": top_queries, "striking_distance": striking_distance}
