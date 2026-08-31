from gadeepdive import report_traffic

DATA = {
    "acquisition": {
        "channels": [
            {"name": "Organic Search", "sessions": 300, "share": 0.75, "engaged_pct": 0.7, "bounce_pct": 0.3, "avg_duration": 120.0},
            {"name": "Direct", "sessions": 100, "share": 0.25, "engaged_pct": 0.4, "bounce_pct": 0.55, "avg_duration": 60.0},
        ],
        "top_referrer": {"source_medium": "github.com / referral", "sessions": 45},
        "first_touch": [
            {"source": "google", "medium": "organic", "sessions": 250, "share": 0.83},
            {"source": "github.com", "medium": "referral", "sessions": 50, "share": 0.17},
        ],
    },
    "geography": {
        "countries": [
            {"name": "United States", "sessions": 400, "share": 0.8, "engaged_pct": 0.7, "engagement_rate": 0.62, "stars": 5},
            {"name": "Germany", "sessions": 100, "share": 0.2, "engaged_pct": 0.2, "engagement_rate": 0.1, "stars": 1},
        ],
        "languages": [
            {"name": "en-us", "sessions": 350, "share": 0.7},
            {"name": "de-de", "sessions": 150, "share": 0.3},
        ],
    },
}

EMPTY_DATA = {"acquisition": {}, "geography": {}}


# ---- acquisition ------------------------------------------------------------------


def test_acquisition_full_shows_channels_referrer_and_first_touch():
    output = report_traffic.acquisition_full(DATA)
    assert "ACQUISITION" in output
    assert "Organic Search" in output
    assert "github.com / referral" in output
    assert "Top Referrer" in output
    assert "First-Touch Attribution" in output
    assert "google / organic" in output


def test_acquisition_full_handles_no_referrer():
    data = {"acquisition": {"channels": [], "top_referrer": None, "first_touch": []}}
    output = report_traffic.acquisition_full(data)
    assert "no referral traffic" in output


def test_acquisition_full_empty_shows_no_data():
    output = report_traffic.acquisition_full(EMPTY_DATA)
    assert "no acquisition data" in output


def test_acquisition_telegram_has_no_box_art():
    output = report_traffic.acquisition_telegram(DATA)
    for box_char in ("╔", "╗", "╚", "╝", "║"):
        assert box_char not in output
    assert "Organic Search" in output
    assert "Top Referrer" in output


# ---- geography --------------------------------------------------------------------


def test_geography_full_shows_countries_with_stars_and_languages():
    output = report_traffic.geography_full(DATA)
    assert "GEOGRAPHY" in output
    assert "United States" in output
    assert "★★★★★" in output
    assert "★☆☆☆☆" in output
    assert "Languages" in output
    assert "en-us" in output


def test_geography_full_empty_shows_no_data():
    output = report_traffic.geography_full(EMPTY_DATA)
    assert "no geography data" in output
    assert "no language data" in output


def test_geography_telegram_has_no_box_art():
    output = report_traffic.geography_telegram(DATA)
    for box_char in ("╔", "╗", "╚", "╝", "║"):
        assert box_char not in output
    assert "United States" in output
    assert "★★★★★" in output
