import sys

import pytest

from gadeepdive.backends import composio as composio_backend
from gadeepdive.backends.composio import (
    ComposioBackend,
    ComposioBackendError,
    _coerce_metric,
    _current_and_previous_ranges,
    _normalize_rows,
)


class FakeComposioClient:
    """Stands in for `composio.Composio` — records calls, returns canned results."""

    def __init__(self, response):
        self.response = response
        self.calls = []

        class _Tools:
            def execute(inner_self, **kwargs):
                self.calls.append(kwargs)
                return self.response

        self.tools = _Tools()


def make_backend(response, **kwargs):
    backend = ComposioBackend(ga4_property_id="900100200", **kwargs)
    backend._client = FakeComposioClient(response)
    return backend


# ---- lazy import ----------------------------------------------------------


def test_composio_module_not_imported_until_client_is_needed():
    backend = ComposioBackend(ga4_property_id="900100200")
    assert "composio" not in sys.modules
    backend._client = FakeComposioClient({"successful": True, "data": {}})
    backend.run_realtime(["activeUsers"])
    assert "composio" not in sys.modules


# ---- pure helpers -----------------------------------------------------------


def test_current_and_previous_ranges_are_equal_length_and_adjacent():
    ranges = _current_and_previous_ranges(7, today=__import__("datetime").date(2026, 8, 31))
    current, previous = ranges
    assert current == {"startDate": "2026-08-24", "endDate": "2026-08-31", "name": "current"}
    assert previous == {"startDate": "2026-08-17", "endDate": "2026-08-23", "name": "previous"}


def test_coerce_metric_integer_type():
    assert _coerce_metric("157", "TYPE_INTEGER") == 157
    assert isinstance(_coerce_metric("157", "TYPE_INTEGER"), int)


def test_coerce_metric_float_type():
    assert _coerce_metric("0.318", "TYPE_FLOAT") == pytest.approx(0.318)


def test_coerce_metric_falls_back_to_raw_value_on_bad_input():
    assert _coerce_metric("not-a-number", "TYPE_INTEGER") == "not-a-number"


def test_normalize_rows_builds_dim_and_metric_dicts():
    data = {
        "dimensionHeaders": [{"name": "sessionDefaultChannelGroup"}],
        "metricHeaders": [{"name": "sessions", "type": "TYPE_INTEGER"}, {"name": "engagementRate", "type": "TYPE_FLOAT"}],
        "rows": [
            {
                "dimensionValues": [{"value": "Direct"}],
                "metricValues": [{"value": "120"}, {"value": "0.308"}],
            }
        ],
    }
    rows = _normalize_rows(data)
    assert rows == [{"sessionDefaultChannelGroup": "Direct", "sessions": 120, "engagementRate": pytest.approx(0.308)}]


def test_normalize_rows_handles_no_rows():
    assert _normalize_rows({"dimensionHeaders": [], "metricHeaders": [], "kind": "analyticsData#runRealtimeReport"}) == []


# ---- run_report -------------------------------------------------------------


def test_run_report_default_date_range_uses_relative_days():
    response = {"successful": True, "data": {"dimensionHeaders": [], "metricHeaders": [], "rows": []}}
    backend = make_backend(response)
    backend.run_report([], ["sessions"], days=7)
    call = backend._client.calls[0]
    assert call["slug"] == composio_backend.RUN_REPORT_SLUG
    assert call["arguments"]["dateRanges"] == [{"startDate": "7daysAgo", "endDate": "today"}]
    assert call["arguments"]["property"] == "properties/900100200"
    assert call["dangerously_skip_version_check"] is True
    assert call["user_id"] == composio_backend.DEFAULT_USER_ID


def test_run_report_compare_previous_uses_named_date_ranges():
    response = {"successful": True, "data": {"dimensionHeaders": [{"name": "dateRange"}], "metricHeaders": [], "rows": []}}
    backend = make_backend(response)
    backend.run_report([], ["sessions"], days=7, extra={"compare_previous": True})
    call = backend._client.calls[0]
    names = [r["name"] for r in call["arguments"]["dateRanges"]]
    assert names == ["current", "previous"]


def test_run_report_includes_dimensions_when_given():
    response = {"successful": True, "data": {"dimensionHeaders": [], "metricHeaders": [], "rows": []}}
    backend = make_backend(response)
    backend.run_report(["country"], ["sessions"], days=7)
    call = backend._client.calls[0]
    assert call["arguments"]["dimensions"] == [{"name": "country"}]


def test_run_report_omits_dimensions_key_when_no_dimensions():
    response = {"successful": True, "data": {"dimensionHeaders": [], "metricHeaders": [], "rows": []}}
    backend = make_backend(response)
    backend.run_report([], ["sessions"], days=7)
    call = backend._client.calls[0]
    assert "dimensions" not in call["arguments"]


def test_run_report_passes_through_limit_and_order_bys_extras():
    response = {"successful": True, "data": {"dimensionHeaders": [], "metricHeaders": [], "rows": []}}
    backend = make_backend(response)
    backend.run_report(["country"], ["sessions"], days=7, extra={"limit": 30, "order_bys": [{"metric": {"metricName": "sessions"}, "desc": True}]})
    call = backend._client.calls[0]
    assert call["arguments"]["limit"] == 30
    assert call["arguments"]["orderBys"][0]["desc"] is True


def test_run_report_explicit_date_ranges_override_days():
    response = {"successful": True, "data": {"dimensionHeaders": [], "metricHeaders": [], "rows": []}}
    backend = make_backend(response)
    explicit = [{"startDate": "2026-01-01", "endDate": "2026-01-07"}]
    backend.run_report([], ["sessions"], days=7, extra={"date_ranges": explicit})
    call = backend._client.calls[0]
    assert call["arguments"]["dateRanges"] == explicit


def test_run_report_raises_on_unsuccessful_result():
    response = {"successful": False, "error": "bad request", "data": {"message": "bad request"}}
    backend = make_backend(response)
    with pytest.raises(ComposioBackendError, match="bad request"):
        backend.run_report([], ["sessions"], days=7)


def test_run_report_returns_normalized_rows():
    response = {
        "successful": True,
        "data": {
            "dimensionHeaders": [{"name": "dateRange"}],
            "metricHeaders": [{"name": "sessions", "type": "TYPE_INTEGER"}],
            "rows": [
                {"dimensionValues": [{"value": "current"}], "metricValues": [{"value": "157"}]},
                {"dimensionValues": [{"value": "previous"}], "metricValues": [{"value": "48"}]},
            ],
        },
    }
    backend = make_backend(response)
    rows = backend.run_report([], ["sessions"], days=7, extra={"compare_previous": True})
    assert rows == [{"dateRange": "current", "sessions": 157}, {"dateRange": "previous", "sessions": 48}]


# ---- run_realtime -----------------------------------------------------------


def test_run_realtime_builds_arguments_and_normalizes():
    response = {
        "successful": True,
        "data": {
            "dimensionHeaders": [],
            "metricHeaders": [{"name": "activeUsers", "type": "TYPE_INTEGER"}],
            "rows": [{"dimensionValues": [], "metricValues": [{"value": "3"}]}],
        },
    }
    backend = make_backend(response)
    rows = backend.run_realtime(["activeUsers"])
    call = backend._client.calls[0]
    assert call["slug"] == composio_backend.RUN_REALTIME_SLUG
    assert call["arguments"] == {"property": "properties/900100200", "metrics": [{"name": "activeUsers"}]}
    assert rows == [{"activeUsers": 3}]


def test_run_realtime_returns_empty_list_when_no_active_users():
    response = {"successful": True, "data": {"kind": "analyticsData#runRealtimeReport"}}
    backend = make_backend(response)
    assert backend.run_realtime(["activeUsers"]) == []


# ---- run_cohort --------------------------------------------------------------


def test_run_cohort_builds_cohort_spec_argument():
    response = {"successful": True, "data": {"dimensionHeaders": [], "metricHeaders": [], "rows": []}}
    backend = make_backend(response)
    spec = {"cohorts": [{"name": "c0", "dateRange": {"startDate": "2026-08-01", "endDate": "2026-08-07"}}]}
    backend.run_cohort(spec, ["cohort"], ["cohortActiveUsers"])
    call = backend._client.calls[0]
    assert call["slug"] == composio_backend.RUN_REPORT_SLUG
    assert call["arguments"]["cohortSpec"] == spec
    assert call["arguments"]["dimensions"] == [{"name": "cohort"}]


# ---- gsc_query ----------------------------------------------------------------


def test_gsc_query_raises_when_no_gsc_site_configured():
    backend = ComposioBackend(ga4_property_id="900100200", gsc_site=None)
    with pytest.raises(ComposioBackendError, match="no GSC site"):
        backend.gsc_query(["query"], days=7)


def test_gsc_query_builds_request_and_shapes_rows():
    response = {
        "successful": True,
        "data": {
            "rows": [
                {"keys": ["how to deploy a repo"], "clicks": 5, "impressions": 100, "ctr": 0.05, "position": 8.2},
            ]
        },
    }
    backend = make_backend(response, gsc_site="sc-domain:repo-atlas.dev")
    rows = backend.gsc_query(["query"], days=7, row_limit=10)
    call = backend._client.calls[0]
    assert call["slug"] == composio_backend.GSC_QUERY_SLUG
    assert call["arguments"]["siteUrl"] == "sc-domain:repo-atlas.dev"
    assert call["arguments"]["rowLimit"] == 10
    assert rows == [{"query": "how to deploy a repo", "clicks": 5, "impressions": 100, "ctr": 0.05, "position": 8.2}]
