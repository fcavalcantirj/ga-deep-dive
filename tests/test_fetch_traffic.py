from gadeepdive import fetch_traffic

from .fixtures import FakeBackend

# ---- acquisition ----------------------------------------------------------------

CHANNEL_ROWS = [
    {
        "sessionDefaultChannelGroup": "Organic Search",
        "sessions": 300,
        "engagedSessions": 210,
        "bounceRate": 0.3,
        "averageSessionDuration": 120.0,
    },
    {
        "sessionDefaultChannelGroup": "Direct",
        "sessions": 100,
        "engagedSessions": 40,
        "bounceRate": 0.55,
        "averageSessionDuration": 60.0,
    },
]

SOURCE_MEDIUM_ROWS = [
    {"sessionSourceMedium": "github.com / referral", "sessions": 45},
    {"sessionSourceMedium": "google / organic", "sessions": 300},
    {"sessionSourceMedium": "gitlab.com / referral", "sessions": 12},
]

FIRST_TOUCH_ROWS = [
    {"firstUserSourceMedium": "google / organic", "sessions": 250},
    {"firstUserSourceMedium": "github.com / referral", "sessions": 50},
]


def _backend(**dim_rows):
    return FakeBackend(dim_rows=dim_rows)


def test_acquisition_channels_have_share_and_engaged_pct():
    backend = _backend(acq_channels=CHANNEL_ROWS)
    result = fetch_traffic.acquisition(backend, days=7)
    channels = result["channels"]
    assert channels[0]["name"] == "Organic Search"
    assert channels[0]["sessions"] == 300
    assert round(channels[0]["share"], 2) == 0.75
    assert round(channels[0]["engaged_pct"], 2) == 0.7
    assert channels[1]["name"] == "Direct"


def test_acquisition_channels_sorted_desc_by_sessions():
    backend = _backend(acq_channels=list(reversed(CHANNEL_ROWS)))
    result = fetch_traffic.acquisition(backend, days=7)
    sessions = [c["sessions"] for c in result["channels"]]
    assert sessions == sorted(sessions, reverse=True)


def test_acquisition_top_referrer_picks_highest_referral_row():
    backend = _backend(acq_channels=[], acq_source_medium=SOURCE_MEDIUM_ROWS, acq_first_touch=[])
    result = fetch_traffic.acquisition(backend, days=7)
    assert result["top_referrer"] == {"source_medium": "github.com / referral", "sessions": 45}


def test_acquisition_top_referrer_none_when_no_referral_rows():
    backend = _backend(acq_source_medium=[{"sessionSourceMedium": "google / organic", "sessions": 300}])
    result = fetch_traffic.acquisition(backend, days=7)
    assert result["top_referrer"] is None


def test_acquisition_first_touch_splits_source_and_medium_with_share():
    backend = _backend(acq_first_touch=FIRST_TOUCH_ROWS)
    result = fetch_traffic.acquisition(backend, days=7)
    first = result["first_touch"][0]
    assert first["source"] == "google"
    assert first["medium"] == "organic"
    assert first["sessions"] == 250
    assert round(first["share"], 2) == round(250 / 300, 2)


def test_acquisition_empty_backend_returns_empty_sections():
    backend = _backend()
    result = fetch_traffic.acquisition(backend, days=7)
    assert result == {"channels": [], "top_referrer": None, "first_touch": []}


def test_acquisition_uses_distinct_row_keys_per_dimension():
    backend = _backend(acq_channels=CHANNEL_ROWS, acq_source_medium=SOURCE_MEDIUM_ROWS, acq_first_touch=FIRST_TOUCH_ROWS)
    fetch_traffic.acquisition(backend, days=7)
    row_keys = {call[4]["row_key"] for call in backend.calls}
    assert row_keys == {"acq_channels", "acq_source_medium", "acq_first_touch"}


# ---- geography --------------------------------------------------------------------

COUNTRY_ROWS = [
    {"country": "United States", "sessions": 400, "engagedSessions": 280, "engagementRate": 0.62},
    {"country": "Germany", "sessions": 100, "engagedSessions": 20, "engagementRate": 0.1},
]

LANGUAGE_ROWS = [
    {"language": "en-us", "sessions": 350},
    {"language": "de-de", "sessions": 150},
]


def test_geography_countries_have_share_and_stars():
    backend = _backend(geo_country=COUNTRY_ROWS)
    result = fetch_traffic.geography(backend, days=7)
    countries = result["countries"]
    assert countries[0]["name"] == "United States"
    assert round(countries[0]["share"], 2) == 0.8
    assert countries[0]["stars"] == 5  # engagementRate 0.62 >= 0.6 threshold
    assert countries[1]["stars"] == 1  # engagementRate 0.1 < 0.15 threshold


def test_geography_star_mapping_thresholds():
    assert fetch_traffic._stars_for_engagement_rate(0.61) == 5
    assert fetch_traffic._stars_for_engagement_rate(0.5) == 4
    assert fetch_traffic._stars_for_engagement_rate(0.35) == 3
    assert fetch_traffic._stars_for_engagement_rate(0.2) == 2
    assert fetch_traffic._stars_for_engagement_rate(0.05) == 1
    assert fetch_traffic._stars_for_engagement_rate(0) == 1


def test_geography_languages_sorted_with_share():
    backend = _backend(geo_language=LANGUAGE_ROWS)
    result = fetch_traffic.geography(backend, days=7)
    languages = result["languages"]
    assert languages[0]["name"] == "en-us"
    assert round(languages[0]["share"], 2) == 0.7


def test_geography_empty_backend_returns_empty_sections():
    backend = _backend()
    result = fetch_traffic.geography(backend, days=7)
    assert result == {"countries": [], "languages": []}
