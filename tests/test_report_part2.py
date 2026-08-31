from gadeepdive import report_part2

SCROLL_DATA = {
    "distribution": [
        {"depth": "10", "count": 500, "share": 0.4},
        {"depth": "25", "count": 300, "share": 0.24},
        {"depth": "50", "count": 200, "share": 0.16},
        {"depth": "75", "count": 150, "share": 0.12},
        {"depth": "90", "count": 80, "share": 0.06},
        {"depth": "100", "count": 20, "share": 0.02},
    ],
    "total_events": 1250,
    "top_pages": [
        {"path": "/docs/api-reference", "completion_rate": 0.9},
        {"path": "/blog/release-notes", "completion_rate": 0.1},
    ],
}

FLOW_DATA = {"entries": [{"path": "/", "entries": 300, "bounce_pct": 0.5}, {"path": "/pricing?ref=hn", "entries": 80, "bounce_pct": 0.35}]}

AUDIENCE_DATA = {"audiences": [{"name": "Repeat Committers", "users": 120, "sessions": 300, "engagement_pct": 0.55}]}

HOURLY_DATA = {
    "hours": [
        {"hour": 3, "sessions": 5, "engaged": 1, "engagement_rate": 0.2, "avg_duration": 10.0},
        {"hour": 9, "sessions": 100, "engaged": 40, "engagement_rate": 0.4, "avg_duration": 60.0},
        {"hour": 21, "sessions": 50, "engaged": 45, "engagement_rate": 0.9, "avg_duration": 200.0},
    ],
    "best_hour": 21,
}

ACQ_TIME_DATA = {"daily": [{"date": "08-26", "users": 120}, {"date": "08-25", "users": 40}, {"date": "08-27", "users": 10}]}

MOBILE_DATA = {"models": [{"model": "iPhone 16", "sessions": 90}, {"model": "Pixel 9", "sessions": 40}]}

DATA = {
    "property": "repo-atlas",
    "days": 7,
    "scroll_depth": SCROLL_DATA,
    "user_flow": FLOW_DATA,
    "audiences": AUDIENCE_DATA,
    "hourly_performance": HOURLY_DATA,
    "acquisition_over_time": ACQ_TIME_DATA,
    "mobile_devices": MOBILE_DATA,
}


# ---- scroll depth ----------------------------------------------------------------


def test_scroll_depth_full_shows_all_buckets():
    output = report_part2.scroll_depth_full(DATA)
    for depth in ("10%", "25%", "50%", "75%", "90%", "100%"):
        assert depth in output


def test_scroll_depth_full_shows_page_completion_rates():
    output = report_part2.scroll_depth_full(DATA)
    assert "/docs/api-reference" in output
    assert "90.0%" in output


def test_scroll_depth_full_no_data_message():
    data = {**DATA, "scroll_depth": {"distribution": [], "total_events": 0, "top_pages": []}}
    output = report_part2.scroll_depth_full(data)
    assert "no scroll data" in output


def test_scroll_depth_telegram_no_box_art():
    output = report_part2.scroll_depth_telegram(DATA)
    for box_char in ("╔", "╗", "╚", "╝", "║"):
        assert box_char not in output


# ---- user flow ---------------------------------------------------------------------


def test_user_flow_full_shows_entries_and_bounce():
    output = report_part2.user_flow_full(DATA)
    assert "/" in output
    assert "50.0%" in output


def test_user_flow_full_empty_message():
    data = {**DATA, "user_flow": {"entries": []}}
    output = report_part2.user_flow_full(data)
    assert "no entry point data" in output


# ---- audiences -----------------------------------------------------------------

def test_audiences_full_shows_audience_row():
    output = report_part2.audiences_full(DATA)
    assert "Repeat Committers" in output


def test_audiences_full_empty_state_keeps_header():
    data = {**DATA, "audiences": {"audiences": []}}
    output = report_part2.audiences_full(data)
    assert "GA4 AUDIENCES" in output
    assert "No custom audiences configured" in output


def test_audiences_telegram_empty_state():
    data = {**DATA, "audiences": {"audiences": []}}
    output = report_part2.audiences_telegram(data)
    assert "No custom audiences configured" in output


# ---- hourly performance ----------------------------------------------------------


def test_hourly_performance_full_marks_best_hour():
    output = report_part2.hourly_performance_full(DATA)
    lines = output.splitlines()
    best_line = next(l for l in lines if "21:00" in l)
    assert "← BEST" in best_line
    other_line = next(l for l in lines if "09:00" in l)
    assert "← BEST" not in other_line


def test_hourly_performance_telegram_marks_best_hour():
    output = report_part2.hourly_performance_telegram(DATA)
    lines = output.splitlines()
    best_line = next(l for l in lines if "21:00" in l)
    assert "← BEST" in best_line


def test_hourly_performance_full_no_data_message():
    data = {**DATA, "hourly_performance": {"hours": [], "best_hour": None}}
    output = report_part2.hourly_performance_full(data)
    assert "no hourly data" in output


# ---- acquisition over time -------------------------------------------------------


def test_acquisition_over_time_full_shows_bars():
    output = report_part2.acquisition_over_time_full(DATA)
    assert "█" in output
    assert "08-26" in output


# ---- mobile devices ---------------------------------------------------------------


def test_mobile_devices_full_shows_models():
    output = report_part2.mobile_devices_full(DATA)
    assert "iPhone 16" in output


def test_mobile_devices_full_no_data_message():
    data = {**DATA, "mobile_devices": {"models": []}}
    output = report_part2.mobile_devices_full(data)
    assert "No mobile device data" in output


def test_mobile_devices_telegram_no_data_message():
    data = {**DATA, "mobile_devices": {"models": []}}
    output = report_part2.mobile_devices_telegram(data)
    assert "No mobile device data" in output


# ---- full monty complete -----------------------------------------------------------


def test_full_monty_complete_full_shows_property_and_period():
    output = report_part2.full_monty_complete_full(DATA)
    assert "REPO-ATLAS" in output
    assert "Last 7 days" in output


def test_full_monty_complete_telegram_shows_property_and_period():
    output = report_part2.full_monty_complete_telegram(DATA)
    assert "REPO-ATLAS" in output
    assert "Last 7 days" in output
