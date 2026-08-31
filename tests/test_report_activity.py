from gadeepdive import report_activity

DATA = {
    "events": {
        "events": [
            {"name": "commit_pushed", "count": 900, "per_user": 3.4},
            {"name": "repo_starred", "count": 500, "per_user": 1.2},
        ]
    },
    "time_patterns": {
        "day_of_week": [
            {"day_name": "Sunday", "sessions": 40, "engaged_pct": 0.25},
            {"day_name": "Monday", "sessions": 100, "engaged_pct": 0.6},
        ],
        "daily": [
            {"date": "08-25", "sessions": 10},
            {"date": "08-26", "sessions": 40},
            {"date": "08-27", "sessions": 30},
        ],
    },
}

EMPTY_DATA = {"events": {}, "time_patterns": {}}


# ---- events -------------------------------------------------------------------------


def test_events_full_lists_events_with_counts():
    output = report_activity.events_full(DATA)
    assert "EVENTS" in output
    assert "commit_pushed" in output
    assert "repo_starred" in output


def test_events_full_empty_shows_no_data():
    output = report_activity.events_full(EMPTY_DATA)
    assert "no event data" in output


def test_events_telegram_has_no_box_art():
    output = report_activity.events_telegram(DATA)
    for box_char in ("╔", "╗", "╚", "╝", "║"):
        assert box_char not in output
    assert "commit_pushed" in output


def test_events_telegram_is_bold_title_with_code_block_table():
    output = report_activity.events_telegram(DATA)
    assert "**⚡ EVENTS**" in output
    assert "```" in output


def test_events_telegram_empty_shows_no_data():
    output = report_activity.events_telegram(EMPTY_DATA)
    assert "no event data" in output


# ---- top-N display cap -------------------------------------------------------------

MANY_EVENTS_DATA = {
    "events": {"events": [{"name": f"event_{i}", "count": 100 - i, "per_user": 1.0} for i in range(20)]},
    "time_patterns": {},
}


def test_events_full_caps_at_fifteen():
    output = report_activity.events_full(MANY_EVENTS_DATA)
    assert "event_14" in output
    assert "event_15" not in output


def test_events_telegram_caps_at_ten():
    output = report_activity.events_telegram(MANY_EVENTS_DATA)
    assert "event_9" in output
    assert "event_10" not in output


# ---- time patterns --------------------------------------------------------------------


def test_time_patterns_full_shows_day_bars_and_sparkline_with_peak():
    output = report_activity.time_patterns_full(DATA)
    assert "TIME PATTERNS" in output
    assert "Sunday" in output
    assert "Monday" in output
    assert "Last 7 Days" in output
    assert "← PEAK" in output
    # peak day is 08-26 (40 sessions)
    peak_line = [line for line in output.splitlines() if "← PEAK" in line][0]
    assert "08-26" in peak_line


def test_time_patterns_full_empty_shows_no_data():
    output = report_activity.time_patterns_full(EMPTY_DATA)
    assert "no day-of-week data" in output
    assert "no daily data" in output


def test_time_patterns_telegram_has_no_box_art():
    output = report_activity.time_patterns_telegram(DATA)
    for box_char in ("╔", "╗", "╚", "╝", "║"):
        assert box_char not in output
    assert "Sunday" in output
    assert "08-26" in output


def test_time_patterns_telegram_is_bold_title_with_code_block_tables():
    output = report_activity.time_patterns_telegram(DATA)
    assert "**🕐 TIME PATTERNS**" in output
    assert "Daily Sessions:" in output
    assert "```" in output


def test_time_patterns_telegram_empty_shows_no_data():
    output = report_activity.time_patterns_telegram(EMPTY_DATA)
    assert "no day-of-week data" in output
    assert "no daily data" in output
