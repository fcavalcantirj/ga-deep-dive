"""Backend protocol every GA4/GSC data source (Composio, native SDK, fakes) implements.

All methods return normalized rows: a list of dicts where each dict maps
dimension names to string values and metric names to numbers, e.g.
`[{"sessionDefaultChannelGroup": "Direct", "sessions": 120, "engagementRate": 0.31}, ...]`.
"""

from typing import Any, Dict, List, Optional, Protocol


class Backend(Protocol):
    def run_report(
        self,
        dimensions: List[str],
        metrics: List[str],
        days: int,
        extra: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Run a GA4 report over the last `days` days, or per `extra` overrides."""
        ...

    def run_realtime(self, metrics: List[str]) -> List[Dict[str, Any]]:
        """Run a GA4 realtime report for the given metrics."""
        ...

    def run_cohort(
        self,
        cohort_spec: Dict[str, Any],
        dimensions: List[str],
        metrics: List[str],
    ) -> List[Dict[str, Any]]:
        """Run a GA4 cohort report (retention analysis)."""
        ...

    def gsc_query(
        self,
        dimensions: List[str],
        days: int,
        row_limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """Run a Google Search Console search analytics query."""
        ...
