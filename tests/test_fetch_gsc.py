from gadeepdive import fetch_gsc

from .fixtures import FakeBackend

GSC_ROWS = [
    {"query": "how to deploy a repo", "clicks": 40, "impressions": 400, "ctr": 0.1, "position": 3.2},
    {"query": "esp-atlas api reference", "clicks": 2, "impressions": 500, "ctr": 0.004, "position": 12.0},
    {"query": "ga4 skill composio", "clicks": 1, "impressions": 300, "ctr": 0.003, "position": 18.5},
    {"query": "unrelated low-impression term", "clicks": 0, "impressions": 5, "ctr": 0.0, "position": 15.0},
]


def _backend_with_site(gsc_rows=None, gsc_site="sc-domain:esp-atlas.com"):
    return FakeBackend(gsc_rows=gsc_rows or [], gsc_site=gsc_site)


# ---- no gsc_site configured -------------------------------------------------------


def test_gsc_report_no_site_returns_unavailable_without_calling_backend():
    backend = FakeBackend(gsc_site=None)
    result = fetch_gsc.gsc_report(backend, days=7)
    assert result == {"available": False}
    assert backend.calls == []


# ---- totals -------------------------------------------------------------------


def test_gsc_report_totals_sum_clicks_and_impressions():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    totals = result["totals"]
    assert totals["clicks"] == 43
    assert totals["impressions"] == 1205


def test_gsc_report_totals_ctr_is_clicks_over_impressions():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    assert round(result["totals"]["ctr"], 4) == round(43 / 1205, 4)


def test_gsc_report_totals_avg_position_is_impression_weighted():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    expected = (3.2 * 400 + 12.0 * 500 + 18.5 * 300 + 15.0 * 5) / 1205
    assert round(result["totals"]["avg_position"], 3) == round(expected, 3)


def test_gsc_report_no_rows_has_zero_totals():
    backend = _backend_with_site(gsc_rows=[])
    result = fetch_gsc.gsc_report(backend, days=7)
    assert result["totals"] == {"clicks": 0, "impressions": 0, "ctr": 0, "avg_position": 0}


# ---- top queries ----------------------------------------------------------------


def test_gsc_report_top_queries_sorted_by_clicks_desc():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    clicks = [q["clicks"] for q in result["top_queries"]]
    assert clicks == sorted(clicks, reverse=True)
    assert result["top_queries"][0]["query"] == "how to deploy a repo"


# ---- striking distance -----------------------------------------------------------


def test_gsc_report_striking_distance_filters_by_position_impressions_and_ctr():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    striking_queries = {q["query"] for q in result["striking_distance"]}
    # position 12.0, impressions 500, ctr 0.004 -> qualifies (pos 8-20, impr>=10, low ctr)
    assert "esp-atlas api reference" in striking_queries
    # position 18.5, impressions 300, ctr 0.003 -> qualifies
    assert "ga4 skill composio" in striking_queries
    # position 3.2 -> too high-ranking, excluded
    assert "how to deploy a repo" not in striking_queries
    # impressions 5 -> below the impression floor, excluded
    assert "unrelated low-impression term" not in striking_queries


def test_gsc_report_striking_distance_sorted_by_impressions_desc():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    impressions = [q["impressions"] for q in result["striking_distance"]]
    assert impressions == sorted(impressions, reverse=True)


def test_gsc_report_striking_distance_empty_when_no_qualifying_queries():
    backend = _backend_with_site(gsc_rows=[{"query": "great fit", "clicks": 50, "impressions": 100, "ctr": 0.5, "position": 1.0}])
    result = fetch_gsc.gsc_report(backend, days=7)
    assert result["striking_distance"] == []


def test_gsc_report_available_true_with_data():
    backend = _backend_with_site(gsc_rows=GSC_ROWS)
    result = fetch_gsc.gsc_report(backend, days=7)
    assert result["available"] is True
