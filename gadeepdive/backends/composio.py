"""Default backend: wraps GA4 + GSC Composio slugs.

`composio` is imported lazily inside methods (never at module import time) so
unit tests can exercise this module without the `composio` package installed.
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_API_KEY_PATH = Path.home() / ".composio.key"
DEFAULT_USER_ID = "7UQIn73xcXnpKIQiaTJzjrCRZk0VznPv"

RUN_REPORT_SLUG = "GOOGLE_ANALYTICS_RUN_REPORT"
RUN_REALTIME_SLUG = "GOOGLE_ANALYTICS_RUN_REALTIME_REPORT"
GSC_QUERY_SLUG = "GOOGLE_SEARCH_CONSOLE_SEARCH_ANALYTICS_QUERY"


class ComposioBackendError(RuntimeError):
    """Raised when a Composio tool execution fails."""


def _current_and_previous_ranges(days: int, today: Optional[date] = None) -> List[Dict[str, str]]:
    """Two named dateRanges: `current` (last `days` days) and the equal-length
    `previous` period immediately before it, for GA4 WoW comparisons."""
    today = today or date.today()
    current_end = today
    current_start = today - timedelta(days=days)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    return [
        {"startDate": current_start.isoformat(), "endDate": current_end.isoformat(), "name": "current"},
        {"startDate": previous_start.isoformat(), "endDate": previous_end.isoformat(), "name": "previous"},
    ]


def _coerce_metric(raw_value: str, metric_type: Optional[str]):
    try:
        if metric_type == "TYPE_INTEGER":
            return int(float(raw_value))
        return float(raw_value)
    except (TypeError, ValueError):
        return raw_value


def _normalize_rows(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    dim_names = [h["name"] for h in data.get("dimensionHeaders", [])]
    metric_headers = data.get("metricHeaders", [])
    rows = []
    for row in data.get("rows", []):
        normalized: Dict[str, Any] = {}
        for i, name in enumerate(dim_names):
            normalized[name] = row["dimensionValues"][i]["value"]
        for i, header in enumerate(metric_headers):
            raw_value = row["metricValues"][i]["value"]
            normalized[header["name"]] = _coerce_metric(raw_value, header.get("type"))
        rows.append(normalized)
    return rows


class ComposioBackend:
    def __init__(
        self,
        ga4_property_id: str,
        gsc_site: Optional[str] = None,
        api_key_path: Optional[Path] = None,
        user_id: str = DEFAULT_USER_ID,
    ):
        self.property = f"properties/{ga4_property_id}"
        self.gsc_site = gsc_site
        self._api_key_path = Path(api_key_path) if api_key_path else DEFAULT_API_KEY_PATH
        self._user_id = user_id
        self._client = None

    def _get_client(self):
        if self._client is None:
            from composio import Composio  # lazy: keep composio out of unit-test deps

            api_key = self._api_key_path.read_text().strip()
            self._client = Composio(api_key=api_key)
        return self._client

    def _execute(self, slug: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        client = self._get_client()
        result = client.tools.execute(
            slug=slug,
            user_id=self._user_id,
            arguments=arguments,
            dangerously_skip_version_check=True,
        )
        if not result.get("successful"):
            raise ComposioBackendError(f"{slug} failed: {result.get('error')}")
        return result.get("data") or {}

    def run_report(
        self,
        dimensions: List[str],
        metrics: List[str],
        days: int,
        extra: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        extra = extra or {}
        date_ranges = extra.get("date_ranges")
        if date_ranges is None:
            if extra.get("compare_previous"):
                date_ranges = _current_and_previous_ranges(days)
            else:
                date_ranges = [{"startDate": f"{days}daysAgo", "endDate": "today"}]

        arguments: Dict[str, Any] = {
            "property": self.property,
            "dateRanges": date_ranges,
            "metrics": [{"name": m} for m in metrics],
        }
        if dimensions:
            arguments["dimensions"] = [{"name": d} for d in dimensions]
        if "limit" in extra:
            arguments["limit"] = extra["limit"]
        if "order_bys" in extra:
            arguments["orderBys"] = extra["order_bys"]

        data = self._execute(RUN_REPORT_SLUG, arguments)
        return _normalize_rows(data)

    def run_realtime(self, metrics: List[str]) -> List[Dict[str, Any]]:
        arguments = {"property": self.property, "metrics": [{"name": m} for m in metrics]}
        data = self._execute(RUN_REALTIME_SLUG, arguments)
        return _normalize_rows(data)

    def run_cohort(
        self,
        cohort_spec: Dict[str, Any],
        dimensions: List[str],
        metrics: List[str],
    ) -> List[Dict[str, Any]]:
        arguments = {
            "property": self.property,
            "cohortSpec": cohort_spec,
            "dimensions": [{"name": d} for d in dimensions],
            "metrics": [{"name": m} for m in metrics],
        }
        data = self._execute(RUN_REPORT_SLUG, arguments)
        return _normalize_rows(data)

    def gsc_query(
        self,
        dimensions: List[str],
        days: int,
        row_limit: int = 25,
    ) -> List[Dict[str, Any]]:
        if not self.gsc_site:
            raise ComposioBackendError("no GSC site configured for this property")

        end = date.today()
        start = end - timedelta(days=days)
        arguments = {
            "siteUrl": self.gsc_site,
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": dimensions,
            "rowLimit": row_limit,
        }
        data = self._execute(GSC_QUERY_SLUG, arguments)
        rows = data.get("rows", [])
        return [
            {
                **dict(zip(dimensions, row.get("keys", []))),
                "clicks": row.get("clicks"),
                "impressions": row.get("impressions"),
                "ctr": row.get("ctr"),
                "position": row.get("position"),
            }
            for row in rows
        ]
