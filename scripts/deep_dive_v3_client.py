"""
GA4 DEEP DIVE v3 — AUTH & GA4 CLIENT
OAuth credential handling and the GA4 API wrapper used by the v3 CLI.
"""

import sys
from typing import Dict, List

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest,
    RunRealtimeReportRequest, OrderBy
)
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from deep_dive_v3_config import SCOPES, CONFIG_DIR, TOKEN_PATH, CREDENTIALS_PATH

# ============================================================================
# AUTH
# ============================================================================

def get_credentials() -> Credentials:
    from google.auth.transport.requests import Request
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    creds = None

    if TOKEN_PATH.exists():
        try: creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except: pass

    if creds and not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
        except: creds = None

    if not creds or not creds.valid:
        if not CREDENTIALS_PATH.exists():
            print(f"❌ Need {CREDENTIALS_PATH}")
            sys.exit(1)
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())

    return creds

# ============================================================================
# GA4 CLIENT
# ============================================================================

class GA4:
    def __init__(self, property_id: str):
        self.property_id = property_id
        self.client = BetaAnalyticsDataClient(credentials=get_credentials())
        self.prop = f"properties/{property_id}"

    def query(self, dims: List[str], mets: List[str], days: int = 30,
              limit: int = 100, order: str = None, desc: bool = True,
              start: str = None, end: str = None) -> List[Dict]:

        dr = DateRange(start_date=start or f"{days}daysAgo", end_date=end or "today")
        req = RunReportRequest(
            property=self.prop,
            date_ranges=[dr],
            dimensions=[Dimension(name=d) for d in dims] if dims else [],
            metrics=[Metric(name=m) for m in mets],
            limit=limit
        )
        if order:
            req.order_bys = [OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order), desc=desc)]

        try:
            resp = self.client.run_report(req)
            return [{**{dims[i]: row.dimension_values[i].value for i in range(len(dims))},
                     **{mets[i]: row.metric_values[i].value for i in range(len(mets))}}
                    for row in resp.rows]
        except Exception as e:
            return [{"_error": str(e)}]

    def totals(self, mets: List[str], days: int = 30) -> Dict:
        r = self.query([], mets, days=days, limit=1)
        return r[0] if r and "_error" not in r[0] else {}

    def realtime(self) -> int:
        try:
            req = RunRealtimeReportRequest(property=self.prop, metrics=[Metric(name="activeUsers")])
            resp = self.client.run_realtime_report(req)
            return int(resp.rows[0].metric_values[0].value) if resp.rows else 0
        except: return 0
