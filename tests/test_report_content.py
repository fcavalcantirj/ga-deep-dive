from gadeepdive import report_content

DATA = {
    "content": {
        "sections": [
            {"section": "docs", "views": 700.0, "users": 450.0, "engagement_pct": 0.54, "page_count": 2},
            {"section": "blog", "views": 100.0, "users": 90.0, "engagement_pct": 0.5, "page_count": 1},
        ],
        "trending_up": [
            {"path": "/docs/api-reference", "current_views": 500, "previous_views": 100, "pct_change": 4.0},
        ],
        "problem_pages": [
            {"path": "/promo/expired-campaign", "sessions": 20, "bounce_pct": 1.0},
        ],
    },
    "segments": {
        "new_vs_returning": [
            {"segment": "new", "sessions": 300, "engagement_pct": 0.4},
            {"segment": "returning", "sessions": 150, "engagement_pct": 0.6},
        ],
        "by_device": [
            {"device": "desktop", "sessions": 250, "share": 0.56, "engagement_pct": 0.5},
            {"device": "mobile", "sessions": 200, "share": 0.44, "engagement_pct": 0.35},
        ],
    },
}

EMPTY_DATA = {"content": {}, "segments": {}}


# ---- content ------------------------------------------------------------------------


def test_content_full_shows_sections_trending_and_problem_pages():
    output = report_content.content_full(DATA)
    assert "CONTENT" in output
    assert "docs" in output
    assert "🔥 Trending Up" in output
    assert "/docs/api-reference" in output
    assert "+400%" in output
    assert "🚨 Problem Pages" in output
    assert "/promo/expired-campaign" in output


def test_content_full_empty_shows_no_data():
    output = report_content.content_full(EMPTY_DATA)
    assert "no content data" in output
    assert "no WoW gainers" in output
    assert "none" in output


def test_content_telegram_has_no_box_art():
    output = report_content.content_telegram(DATA)
    for box_char in ("╔", "╗", "╚", "╝", "║"):
        assert box_char not in output
    assert "docs" in output


# ---- user segments --------------------------------------------------------------------


def test_user_segments_full_shows_new_vs_returning_and_device_bars():
    output = report_content.user_segments_full(DATA)
    assert "USER SEGMENTS" in output
    assert "new" in output
    assert "returning" in output
    assert "By Device" in output
    assert "desktop" in output


def test_user_segments_full_empty_shows_no_data():
    output = report_content.user_segments_full(EMPTY_DATA)
    assert "no segment data" in output
    assert "no device data" in output


def test_user_segments_telegram_has_no_box_art():
    output = report_content.user_segments_telegram(DATA)
    for box_char in ("╔", "╗", "╚", "╝", "║"):
        assert box_char not in output
    assert "desktop" in output
