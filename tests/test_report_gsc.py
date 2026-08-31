from gadeepdive import report_gsc

AVAILABLE_DATA = {
    "property": "esp-atlas",
    "gsc": {
        "available": True,
        "totals": {"clicks": 43, "impressions": 1205, "ctr": 0.0357, "avg_position": 9.9},
        "top_queries": [{"query": "how to deploy a repo", "clicks": 40, "impressions": 400, "ctr": 0.1, "position": 3.2}],
        "striking_distance": [{"query": "esp-atlas api reference", "clicks": 2, "impressions": 500, "ctr": 0.004, "position": 12.0}],
    },
}

NO_SITE_DATA = {"property": "abecmed", "gsc": {"available": False}}

SUPPRESSED_DATA = {"property": "abecmed", "gsc": None}


# ---- available ------------------------------------------------------------------


def test_gsc_full_shows_totals_and_top_queries():
    output = report_gsc.gsc_full(AVAILABLE_DATA)
    assert "43" in output
    assert "how to deploy a repo" in output


def test_gsc_full_shows_striking_distance():
    output = report_gsc.gsc_full(AVAILABLE_DATA)
    assert "esp-atlas api reference" in output
    assert "Striking Distance" in output


def test_gsc_telegram_shows_totals():
    output = report_gsc.gsc_telegram(AVAILABLE_DATA)
    assert "how to deploy a repo" in output


def test_gsc_full_no_query_data_keeps_header():
    data = {"property": "esp-atlas", "gsc": {"available": True, "totals": {}, "top_queries": [], "striking_distance": []}}
    output = report_gsc.gsc_full(data)
    assert "Top Queries" in output
    assert "no query data" in output


# ---- no site configured -----------------------------------------------------------


def test_gsc_full_no_site_shows_graceful_message_with_property_name():
    output = report_gsc.gsc_full(NO_SITE_DATA)
    assert "No Search Console site configured for abecmed" in output


def test_gsc_telegram_no_site_shows_graceful_message():
    output = report_gsc.gsc_telegram(NO_SITE_DATA)
    assert "No Search Console site configured for abecmed" in output


# ---- suppressed (--no-gsc) ---------------------------------------------------------


def test_gsc_full_suppressed_returns_empty_string():
    assert report_gsc.gsc_full(SUPPRESSED_DATA) == ""


def test_gsc_telegram_suppressed_returns_empty_string():
    assert report_gsc.gsc_telegram(SUPPRESSED_DATA) == ""


def test_gsc_full_missing_key_returns_empty_string():
    assert report_gsc.gsc_full({"property": "abecmed"}) == ""
