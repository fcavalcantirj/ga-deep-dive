from gadeepdive import fetch_technology

from .fixtures import FakeBackend

BROWSER_ROWS = [
    {"browser": "Chrome", "sessions": 400, "engagedSessions": 280},
    {"browser": "Safari", "sessions": 100, "engagedSessions": 40},
]

RESOLUTION_ROWS = [
    {"screenResolution": "1920x1080", "sessions": 300},
    {"screenResolution": "390x844", "sessions": 150},
]


def _backend(**dim_rows):
    return FakeBackend(dim_rows=dim_rows)


def test_browsers_sorted_desc_with_engaged_pct():
    backend = _backend(tech_browser=BROWSER_ROWS)
    result = fetch_technology.technology(backend, days=7)
    browsers = result["browsers"]
    assert browsers[0]["name"] == "Chrome"
    assert round(browsers[0]["engaged_pct"], 2) == 0.7


def test_resolutions_sorted_desc_by_sessions():
    backend = _backend(tech_resolution=RESOLUTION_ROWS)
    result = fetch_technology.technology(backend, days=7)
    resolutions = result["resolutions"]
    assert resolutions[0]["resolution"] == "1920x1080"


def test_technology_empty_backend_returns_empty_lists():
    backend = _backend()
    result = fetch_technology.technology(backend, days=7)
    assert result == {"browsers": [], "resolutions": []}
