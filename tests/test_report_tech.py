from gadeepdive import report_tech

DATA = {
    "technology": {
        "browsers": [
            {"name": "Chrome", "sessions": 400, "engaged_pct": 0.7},
            {"name": "Safari", "sessions": 100, "engaged_pct": 0.4},
        ],
        "resolutions": [
            {"resolution": "1920x1080", "sessions": 300},
            {"resolution": "390x844", "sessions": 150},
        ],
    },
    "insights": [
        {"icon": "🔴", "message": "Organic Search drives 90% of sessions", "action": "Diversify acquisition channels"},
        {"icon": "🟢", "message": "Sessions up 100% WoW", "action": "Double down on Organic Search"},
    ],
}

EMPTY_DATA = {"technology": {}, "insights": []}


# ---- technology -----------------------------------------------------------------------


def test_technology_full_shows_browsers_and_resolutions():
    output = report_tech.technology_full(DATA)
    assert "TECHNOLOGY" in output
    assert "Chrome" in output
    assert "Top Resolutions" in output
    assert "1920x1080" in output


def test_technology_full_empty_shows_no_data():
    output = report_tech.technology_full(EMPTY_DATA)
    assert "no browser data" in output
    assert "no resolution data" in output


def test_technology_telegram_has_no_box_art():
    output = report_tech.technology_telegram(DATA)
    for box_char in ("╔", "╗", "╚", "╝", "║"):
        assert box_char not in output
    assert "Chrome" in output


# ---- insights -----------------------------------------------------------------------------


def test_insights_full_shows_icon_message_and_arrow_action():
    output = report_tech.insights_full(DATA)
    assert "ACTIONABLE INSIGHTS" in output
    assert "🔴" in output
    assert "Organic Search drives 90% of sessions" in output
    assert "→ Diversify acquisition channels" in output


def test_insights_full_empty_shows_no_insights():
    output = report_tech.insights_full(EMPTY_DATA)
    assert "no insights" in output


def test_insights_telegram_has_no_box_art_and_shows_arrow():
    output = report_tech.insights_telegram(DATA)
    for box_char in ("╔", "╗", "╚", "╝", "║"):
        assert box_char not in output
    assert "→" in output
