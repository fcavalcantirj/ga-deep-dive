from gadeepdive import fetch_segments

from .fixtures import FakeBackend

NVR_ROWS = [
    {"newVsReturning": "new", "sessions": 300, "engagementRate": 0.4},
    {"newVsReturning": "returning", "sessions": 150, "engagementRate": 0.6},
]

DEVICE_ROWS = [
    {"deviceCategory": "desktop", "sessions": 250, "engagementRate": 0.5},
    {"deviceCategory": "mobile", "sessions": 200, "engagementRate": 0.35},
]


def _backend(**dim_rows):
    return FakeBackend(dim_rows=dim_rows)


def test_new_vs_returning_returns_sessions_and_engagement():
    backend = _backend(segments_new_returning=NVR_ROWS)
    result = fetch_segments.user_segments(backend, days=7)
    segments = {s["segment"]: s for s in result["new_vs_returning"]}
    assert segments["new"]["sessions"] == 300
    assert segments["returning"]["engagement_pct"] == 0.6


def test_by_device_has_share_and_engagement():
    backend = _backend(segments_device=DEVICE_ROWS)
    result = fetch_segments.user_segments(backend, days=7)
    devices = {d["device"]: d for d in result["by_device"]}
    assert round(devices["desktop"]["share"], 2) == round(250 / 450, 2)
    assert devices["mobile"]["engagement_pct"] == 0.35


def test_by_device_sorted_desc_by_sessions():
    backend = _backend(segments_device=list(reversed(DEVICE_ROWS)))
    result = fetch_segments.user_segments(backend, days=7)
    sessions = [d["sessions"] for d in result["by_device"]]
    assert sessions == sorted(sessions, reverse=True)


def test_user_segments_empty_backend_returns_empty_lists():
    backend = _backend()
    result = fetch_segments.user_segments(backend, days=7)
    assert result == {"new_vs_returning": [], "by_device": []}
