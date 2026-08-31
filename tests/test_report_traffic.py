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
    assert "Organic" in output  # truncated to fit the phone-width column
    assert "Top Referrer" in output


def test_acquisition_telegram_is_bold_title_with_code_block_table():
    output = report_traffic.acquisition_telegram(DATA)
    assert "**🚦 ACQUISITION**" in output
    assert "```" in output
    assert "Direct" in output


def test_acquisition_telegram_shows_top_referrer_as_source_medium_and_sessions():
    output = report_traffic.acquisition_telegram(DATA)
    assert "github.com / referral — 45 sessions" in output


def test_acquisition_telegram_first_touch_shows_source_slash_medium_not_none():
    output = report_traffic.acquisition_telegram(DATA)
    assert "google/organic" in output
    assert "None" not in output


def test_acquisition_telegram_empty_shows_no_data():
    output = report_traffic.acquisition_telegram(EMPTY_DATA)
    assert "no acquisition data" in output
    assert "Top Referrer: no referral traffic" in output
    assert "First-Touch Attribution: no data" in output


def test_acquisition_telegram_table_rows_stay_within_phone_width():
    output = report_traffic.acquisition_telegram(DATA)
    in_block = False
    for line in output.splitlines():
        if line.strip() == "```":
            in_block = not in_block
            continue
        if in_block:
            assert len(line) <= 30, f"line exceeds 30 cols: {line!r}"


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
    assert "United" in output  # truncated to fit the phone-width column
    assert "★★★★★" in output


def test_geography_telegram_is_bold_title_with_code_block_table():
    output = report_traffic.geography_telegram(DATA)
    assert "**🌍 GEOGRAPHY**" in output
    assert "```" in output
    assert "en-us" in output


def test_geography_telegram_empty_shows_no_data():
    output = report_traffic.geography_telegram(EMPTY_DATA)
    assert "no geography data" in output
    assert "Languages: no language data" in output


# ---- top-N display caps -----------------------------------------------------------

MANY_COUNTRIES_DATA = {
    "acquisition": {},
    "geography": {
        "countries": [{"name": f"Country {i}", "sessions": 100 - i, "share": 0.1, "engaged_pct": 0.5, "engagement_rate": 0.5, "stars": 3} for i in range(15)],
        "languages": [],
    },
}

MANY_FIRST_TOUCH_DATA = {
    "acquisition": {
        "channels": [],
        "top_referrer": None,
        "first_touch": [{"source": f"source{i}", "medium": "organic", "sessions": 100 - i, "share": 0.05} for i in range(12)],
    },
    "geography": {},
}


def test_geography_full_caps_countries_at_ten():
    output = report_traffic.geography_full(MANY_COUNTRIES_DATA)
    assert "Country 9" in output
    assert "Country 10" not in output


def test_geography_telegram_caps_countries_at_ten():
    output = report_traffic.geography_telegram(MANY_COUNTRIES_DATA)
    # session counts are 100..86 for rows 0..14 (one per country); only the
    # first ten rows (sessions 100..91) should survive the cap.
    assert "91" in output
    assert "90" not in output


def test_acquisition_full_caps_first_touch_at_eight():
    output = report_traffic.acquisition_full(MANY_FIRST_TOUCH_DATA)
    assert "source7" in output
    assert "source8" not in output


def test_acquisition_telegram_caps_first_touch_at_seven():
    output = report_traffic.acquisition_telegram(MANY_FIRST_TOUCH_DATA)
    assert "source6" in output
    assert "source7" not in output
