"""
GA4 DEEP DIVE v2 — AUTH & GA4 CLIENT
OAuth credential handling and the GA4 API wrapper used by the v2 CLI.
"""

import sys
from typing import Dict, List

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest,
    RunRealtimeReportRequest, OrderBy, FilterExpression
)
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from deep_dive_v2_config import SCOPES, CONFIG_DIR, TOKEN_PATH, CREDENTIALS_PATH

# ============================================================================
# AUTH
# ============================================================================

def get_credentials() -> Credentials:
    """Get or refresh OAuth credentials."""
    from google.auth.transport.requests import Request

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    creds = None

    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception as e:
            print(f"⚠️ Token load error: {e}")
            creds = None

    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                TOKEN_PATH.write_text(creds.to_json())
            except Exception as e:
                print(f"⚠️ Token refresh failed: {e}")
                creds = None

    if not creds or not creds.valid:
        if not CREDENTIALS_PATH.exists():
            print(f"❌ Need credentials.json at: {CREDENTIALS_PATH}")
            sys.exit(1)
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())

    return creds

# ============================================================================
# GA4 API WRAPPER
# ============================================================================

class GA4Client:
    """Wrapper for GA4 API with conveniences."""

    def __init__(self, property_id: str):
        self.property_id = property_id
        self.client = BetaAnalyticsDataClient(credentials=get_credentials())
        self.property = f"properties/{property_id}"

    def report(self, dimensions: List[str], metrics: List[str],
               days: int = 30, start_date: str = None, end_date: str = None,
               limit: int = 100, order_by: str = None, desc: bool = True,
               dim_filter: FilterExpression = None) -> List[Dict]:
        """Run a report and return list of dicts."""

        if start_date and end_date:
            date_range = DateRange(start_date=start_date, end_date=end_date)
        else:
            date_range = DateRange(start_date=f"{days}daysAgo", end_date="today")

        request = RunReportRequest(
            property=self.property,
            date_ranges=[date_range],
            dimensions=[Dimension(name=d) for d in dimensions] if dimensions else [],
            metrics=[Metric(name=m) for m in metrics],
            limit=limit
        )

        if order_by:
            request.order_bys = [OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order_by), desc=desc)]
        if dim_filter:
            request.dimension_filter = dim_filter

        try:
            response = self.client.run_report(request)
            results = []
            for row in response.rows:
                r = {}
                for i, d in enumerate(dimensions):
                    r[d] = row.dimension_values[i].value
                for i, m in enumerate(metrics):
                    r[m] = row.metric_values[i].value
                results.append(r)
            return results
        except Exception as e:
            return [{"_error": str(e)}]

    def realtime(self) -> int:
        """Get realtime active users."""
        try:
            req = RunRealtimeReportRequest(
                property=self.property,
                metrics=[Metric(name="activeUsers")]
            )
            resp = self.client.run_realtime_report(req)
            return int(resp.rows[0].metric_values[0].value) if resp.rows else 0
        except:
            return 0

    def metrics_only(self, metrics: List[str], days: int = 30) -> Dict:
        """Get just metrics, no dimensions."""
        results = self.report([], metrics, days=days, limit=1)
        return results[0] if results else {}
