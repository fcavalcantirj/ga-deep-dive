import json

import pytest

from gadeepdive import report

SAMPLE_DATA = {
    "property": "repo-atlas",
    "days": 7,
    "generated_at": "2026-08-31 12:00 UTC",
    "realtime": {"active_users": 3},
    "executive": {
        "current": {
            "sessions": 157,
            "activeUsers": 96,
            "newUsers": 40,
            "engagedSessions": 88,
            "engagementRate": 0.318,
            "bounceRate": 0.42,
            "averageSessionDuration": 145.0,
            "screenPageViewsPerSession": 2.4,
            "screenPageViews": 377,
        },
        "previous": {
            "sessions": 48,
            "activeUsers": 30,
            "newUsers": 12,
            "engagedSessions": 20,
            "engagementRate": 0.25,
            "bounceRate": 0.5,
            "averageSessionDuration": 90.0,
            "screenPageViewsPerSession": 1.9,
            "screenPageViews": 91,
        },
    },
    "activity": {
        "active1DayUsers": 12,
        "active7DayUsers": 60,
        "active28DayUsers": 200,
        "dauPerWau": 0.2,
        "dauPerMau": 0.06,
    },
    "health": {
        "scores": {
            "Growth": 82,
            "Content": None,
            "Engagement": 32,
            "Mobile": None,
            "Geo Diversity": None,
            "Retention": 30,
            "Traffic Diversity": None,
        },
        "overall": 48,
        "grade": "C",
    },
}


def sample_data_with_new_metric():
    """A variant where sessions has no previous value at all (NEW case)."""
    data = json.loads(json.dumps(SAMPLE_DATA))
    del data["executive"]["previous"]["sessions"]
    return data


# ---- delta_arrow --------------------------------------------------------------


def test_delta_arrow_new_when_no_previous_and_positive_current():
    assert report.delta_arrow(100, None) == "NEW"
    assert report.delta_arrow(100, 0) == "NEW"


def test_delta_arrow_dash_when_no_previous_and_zero_current():
    assert report.delta_arrow(0, None) == "—"
    assert report.delta_arrow(0, 0) == "—"


def test_delta_arrow_strong_growth_is_green():
    assert report.delta_arrow(150, 100) == "🟢 +50%"


def test_delta_arrow_mild_growth_is_up_arrow():
    assert report.delta_arrow(105, 100) == "↑5%"


def test_delta_arrow_strong_decline_is_red():
    assert report.delta_arrow(50, 100) == "🔴 -50%"


def test_delta_arrow_mild_decline_is_down_arrow():
    assert report.delta_arrow(95, 100) == "↓5%"


def test_delta_arrow_flat_is_neutral():
    assert report.delta_arrow(100, 100) == "→"


def test_delta_arrow_reverse_flips_direction_for_bounce_rate_style_metrics():
    # Bounce rate dropping (good) should read as growth, not decline.
    assert report.delta_arrow(50, 100, reverse=True) == "🟢 +50%"
    # Bounce rate rising (bad) should read as decline.
    assert report.delta_arrow(150, 100, reverse=True) == "🔴 -50%"


# ---- render_full ----------------------------------------------------------------


def test_render_full_includes_banner_with_property_and_period():
    output = report.render_full(SAMPLE_DATA)
    assert "REPO-ATLAS" in output
    assert "Last 7 days" in output
    assert "2026-08-31 12:00 UTC" in output
    assert "╔" in output and "╚" in output


def test_render_full_includes_live_now():
    output = report.render_full(SAMPLE_DATA)
    assert "🟢 LIVE NOW: 3 active users" in output


def test_render_full_live_now_singular_user():
    data = json.loads(json.dumps(SAMPLE_DATA))
    data["realtime"]["active_users"] = 1
    output = report.render_full(data)
    assert "1 active user " in output or "1 active user\n" in output or "1 active user" in output
    assert "1 active users" not in output


def test_render_full_executive_summary_shows_wow_arrows():
    output = report.render_full(SAMPLE_DATA)
    assert "Sessions" in output
    # 157 vs 48 => strong growth => green arrow
    assert "🟢" in output


def test_render_full_executive_summary_shows_new_when_no_previous_value():
    output = report.render_full(sample_data_with_new_metric())
    assert "NEW" in output


def test_render_full_health_dashboard_sorted_best_to_worst_with_stubs_last():
    output = report.render_full(SAMPLE_DATA)
    dashboard = output[output.index("HEALTH DASHBOARD"):]
    growth_pos = dashboard.index("Growth")
    engagement_pos = dashboard.index("Engagement")
    retention_pos = dashboard.index("Retention")
    content_pos = dashboard.index("Content")
    assert growth_pos < engagement_pos < retention_pos
    assert content_pos > retention_pos  # None-score stub sorts after real scores


def test_render_full_health_dashboard_shows_no_data_for_stubs():
    output = report.render_full(SAMPLE_DATA)
    assert "(no data yet" in output


def test_render_full_shows_overall_score_and_grade():
    output = report.render_full(SAMPLE_DATA)
    assert "OVERALL SCORE: 48/100 (Grade C)" in output


def test_render_full_overall_na_when_no_scores_available():
    data = json.loads(json.dumps(SAMPLE_DATA))
    data["health"] = {"scores": {k: None for k in report.HEALTH_LABELS}, "overall": None, "grade": "N/A"}
    output = report.render_full(data)
    assert "OVERALL SCORE: N/A (Grade N/A)" in output


# ---- render_telegram -------------------------------------------------------------


def test_render_telegram_has_no_box_art():
    output = report.render_telegram(SAMPLE_DATA)
    for box_char in ("╔", "╗", "╚", "╝", "║"):
        assert box_char not in output


def test_render_telegram_still_has_key_content():
    output = report.render_telegram(SAMPLE_DATA)
    assert "REPO-ATLAS" in output
    assert "LIVE NOW" in output
    assert "EXECUTIVE SUMMARY" in output
    assert "HEALTH DASHBOARD" in output
    assert "OVERALL" in output


def test_render_telegram_shows_new_when_no_previous_value():
    output = report.render_telegram(sample_data_with_new_metric())
    assert "NEW" in output


def test_render_telegram_shows_no_data_for_stub_scores():
    output = report.render_telegram(SAMPLE_DATA)
    assert "no data yet" in output


# ---- render_json ------------------------------------------------------------------


def test_render_json_returns_expected_shape():
    result = report.render_json(SAMPLE_DATA)
    assert result["property"] == "repo-atlas"
    assert result["days"] == 7
    assert result["live_now"] == {"active_users": 3}
    assert result["executive_summary"]["current"]["sessions"] == 157
    assert result["executive_summary"]["previous"]["sessions"] == 48
    assert result["user_activity"]["active1DayUsers"] == 12
    assert result["health"]["scores"]["Growth"] == 82
    assert result["health"]["overall"] == 48
    assert result["health"]["grade"] == "C"


def test_render_json_is_json_serializable():
    result = report.render_json(SAMPLE_DATA)
    reparsed = json.loads(json.dumps(result))
    assert reparsed["property"] == "repo-atlas"


# ---- dispatcher --------------------------------------------------------------------


def test_render_dispatches_to_full_by_default():
    assert report.render(SAMPLE_DATA) == report.render_full(SAMPLE_DATA)


def test_render_dispatches_to_telegram():
    assert report.render(SAMPLE_DATA, "telegram") == report.render_telegram(SAMPLE_DATA)


def test_render_dispatches_to_json():
    assert report.render(SAMPLE_DATA, "json") == report.render_json(SAMPLE_DATA)


def test_render_unknown_mode_raises():
    with pytest.raises(ValueError, match="unknown render mode"):
        report.render(SAMPLE_DATA, "carrier-pigeon")


# ---- other formatting helpers --------------------------------------------------------


def test_fmt_num_formats_thousands_and_millions():
    assert report.fmt_num(500) == "500"
    assert report.fmt_num(1500) == "1.5K"
    assert report.fmt_num(2_500_000) == "2.5M"


def test_bar_renders_filled_and_empty_blocks():
    assert report.bar(50, 100, 10) == "█████░░░░░"
    assert report.bar(0, 100, 10) == "░" * 10
    assert report.bar(100, 100, 10) == "█" * 10


def test_bar_handles_zero_max_value():
    assert report.bar(0, 0, 10) == "░" * 10


def test_status_icon_warning_range():
    data = json.loads(json.dumps(SAMPLE_DATA))
    data["health"]["scores"]["Growth"] = 65
    output = report.render_full(data)
    dashboard = output[output.index("HEALTH DASHBOARD"):]
    assert "⚠️" in dashboard
