"""Optional native `google-analytics-data` OAuth backend (behind --backend native).

Not implemented in R1 — Composio is the default backend and the only one wired
to real data. This stub keeps the Backend protocol satisfiable so `--backend
native` fails loudly and clearly instead of silently falling back to Composio.
"""

from typing import Any, Dict, List, Optional

_NOT_IMPLEMENTED = (
    "native backend is not implemented yet — use --backend composio "
    "(see SPEC.md: native google-analytics-data OAuth backend is a future round)"
)


class NativeBackend:
    def __init__(self, ga4_property_id: str, gsc_site: Optional[str] = None):
        self.ga4_property_id = ga4_property_id
        self.gsc_site = gsc_site

    def run_report(
        self,
        dimensions: List[str],
        metrics: List[str],
        days: int,
        extra: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def run_realtime(self, metrics: List[str]) -> List[Dict[str, Any]]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def run_cohort(
        self,
        cohort_spec: Dict[str, Any],
        dimensions: List[str],
        metrics: List[str],
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def gsc_query(
        self,
        dimensions: List[str],
        days: int,
        row_limit: int = 25,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError(_NOT_IMPLEMENTED)
