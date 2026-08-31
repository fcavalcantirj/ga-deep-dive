from gadeepdive import fetch_gsc

from .fixtures import FakeBackend

GSC_ROWS = [
    {"query": "how to flash esp32 firmware", "clicks": 40, "impressions": 400, "ctr": 0.1, "position": 3.2},
    {"query": "esp32 marauder firmware", "clicks": 5, "impressions": 620, "ctr": 0.008, "position": 8.3},
    {"query": "esp-atlas api reference", "clicks": 2, "impressions": 500, "ctr": 0.004, "position": 12.0},
    {"query": "ga4 skill composio setup", "clicks": 1, "impressions": 300, "ctr": 0.003, "position": 18.5},
    {"query": "boundary five impressions query", "clicks": 0, "impressions": 5, "ctr": 0.0, "position": 15.0},
    {"query": "just below the impression floor", "clicks": 0, "impressions": 4, "ctr": 0.0, "position": 10.0},
    {"query": "high ctr but still worth surfacing", "clicks": 50, "impressions": 500, "ctr": 0.5, "position": 9.0},
]


def _backend_with_site(gsc_rows=None, gsc_site="sc-domain:esp-atlas.com"):
    return FakeBackend(gsc_rows=gsc_rows or [], gsc_site=gsc_site)


# ---- no gsc_site configured -------------------------------------------------------


def test_gsc_report_no_site_returns_unavailable_without_calling_backend():
    backend = FakeBackend(gsc_site=None)
    result = fetch_gsc.gsc_report(backend, days=7)
    assert result == {"available": False}
    assert backend.calls == []


# ---- row limit --------------------------------------------------------------------


def test_gsc_report_queries_with_row_limit_100_by_default():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    fetch_gsc.gsc_report(backend, days=7)
    call = next(c for c in backend.calls if c[0] == "gsc_query")
    assert call == ("gsc_query", ["query"], 7, 100)


def test_gsc_report_row_limit_is_overridable():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    fetch_gsc.gsc_report(backend, days=7, row_limit=50)
    call = next(c for c in backend.calls if c[0] == "gsc_query")
    assert call[3] == 50


# ---- totals -------------------------------------------------------------------


def test_gsc_report_totals_sum_clicks_and_impressions():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    totals = result["totals"]
    assert totals["clicks"] == sum(q["clicks"] for q in GSC_ROWS)
    assert totals["impressions"] == sum(q["impressions"] for q in GSC_ROWS)


def test_gsc_report_totals_ctr_is_clicks_over_impressions():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    total_clicks = sum(q["clicks"] for q in GSC_ROWS)
    total_impressions = sum(q["impressions"] for q in GSC_ROWS)
    assert round(result["totals"]["ctr"], 4) == round(total_clicks / total_impressions, 4)


def test_gsc_report_totals_avg_position_is_impression_weighted():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    total_impressions = sum(q["impressions"] for q in GSC_ROWS)
    expected = sum(q["position"] * q["impressions"] for q in GSC_ROWS) / total_impressions
    assert round(result["totals"]["avg_position"], 3) == round(expected, 3)


def test_gsc_report_no_rows_has_zero_totals():
    backend = _backend_with_site(gsc_rows=[])
    result = fetch_gsc.gsc_report(backend, days=7)
    assert result["totals"] == {"clicks": 0, "impressions": 0, "ctr": 0, "avg_position": 0}


# ---- top queries: fetch layer keeps the FULL sorted set ---------------------------


def test_gsc_report_top_queries_sorted_by_clicks_desc():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    clicks = [q["clicks"] for q in result["top_queries"]]
    assert clicks == sorted(clicks, reverse=True)
    assert result["top_queries"][0]["query"] == "high ctr but still worth surfacing"


def test_gsc_report_top_queries_is_not_truncated_at_fetch_layer():
    many_rows = [{"query": f"query {i}", "clicks": i, "impressions": 100, "ctr": 0.01, "position": 5.0} for i in range(25)]
    backend = _backend_with_site(gsc_rows=many_rows)
    result = fetch_gsc.gsc_report(backend, days=7)
    assert len(result["top_queries"]) == 25  # display-layer caps this, not the fetcher


def test_gsc_report_blank_query_gets_not_set_label():
    backend = _backend_with_site(gsc_rows=[{"query": "", "clicks": 1, "impressions": 10, "ctr": 0.1, "position": 5.0}])
    result = fetch_gsc.gsc_report(backend, days=7)
    assert result["top_queries"][0]["query"] == "(not set)"


# ---- striking distance: position 8-20, impressions >= 5, no CTR filter ------------


def test_gsc_report_striking_distance_filters_by_position_and_impressions():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    striking_queries = {q["query"] for q in result["striking_distance"]}
    # pos 8.3, impressions 620 -> qualifies (the GOLDEN-TARGET reference candidate)
    assert "esp32 marauder firmware" in striking_queries
    # pos 12.0, impressions 500 -> qualifies
    assert "esp-atlas api reference" in striking_queries
    # pos 18.5, impressions 300 -> qualifies (upper boundary of the window)
    assert "ga4 skill composio setup" in striking_queries
    # pos 9.0, impressions 500, ctr 0.5 -> qualifies: CTR is no longer a filter
    assert "high ctr but still worth surfacing" in striking_queries
    # impressions == 5 -> meets the floor (>=5), qualifies
    assert "boundary five impressions query" in striking_queries
    # pos 3.2 -> too high-ranking (outside 8-20), excluded
    assert "how to flash esp32 firmware" not in striking_queries
    # impressions == 4 -> below the floor, excluded
    assert "just below the impression floor" not in striking_queries


def test_gsc_report_striking_distance_sorted_by_impressions_desc():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    impressions = [q["impressions"] for q in result["striking_distance"]]
    assert impressions == sorted(impressions, reverse=True)


def test_gsc_report_striking_distance_capped_at_ten():
    many_qualifying = [
        {"query": f"striking query {i}", "clicks": 1, "impressions": 100 - i, "ctr": 0.01, "position": 10.0} for i in range(15)
    ]
    backend = _backend_with_site(gsc_rows=many_qualifying)
    result = fetch_gsc.gsc_report(backend, days=7)
    assert len(result["striking_distance"]) == 10
    # keeps the highest-impression 10, sorted desc
    assert result["striking_distance"][0]["query"] == "striking query 0"
    assert result["striking_distance"][-1]["query"] == "striking query 9"


def test_gsc_report_striking_distance_empty_when_no_qualifying_queries():
    backend = _backend_with_site(gsc_rows=[{"query": "great fit", "clicks": 50, "impressions": 100, "ctr": 0.5, "position": 1.0}])
    result = fetch_gsc.gsc_report(backend, days=7)
    assert result["striking_distance"] == []


def test_gsc_report_available_true_with_data():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    assert result["available"] is True
