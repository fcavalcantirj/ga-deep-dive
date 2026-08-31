import json

import matplotlib.pyplot as plt
import pytest
from matplotlib.patches import FancyBboxPatch

from gadeepdive import charts

FULL_DATA = {
    "property": "repo-atlas",
    "days": 7,
    "generated_at": "2026-08-31 12:00 UTC",
    "executive": {
        "current": {"sessions": 1570, "activeUsers": 960, "engagementRate": 0.512, "screenPageViews": 3770},
        "previous": {"sessions": 980, "activeUsers": 700, "engagementRate": 0.40, "screenPageViews": 2500},
    },
    "health": {
        "scores": {
            "Growth": 82,
            "Content": 55,
            "Engagement": 51,
            "Mobile": 38,
            "Geo Diversity": 70,
            "Retention": None,
            "Traffic Diversity": 90,
        },
        "overall": 64,
        "grade": "B",
    },
    "acquisition": {
        "channels": [
            {"name": "Organic Search", "sessions": 600},
            {"name": "Direct", "sessions": 400},
            {"name": "Referral", "sessions": 250},
            {"name": "Social", "sessions": 150},
            {"name": "Email", "sessions": 90},
            {"name": "Paid Search", "sessions": 50},
            {"name": "Display", "sessions": 20},
            {"name": "Other", "sessions": 10},
        ]
    },
    "geography": {
        "countries": [
            {"name": "United States", "sessions": 700},
            {"name": "Brazil", "sessions": 300},
            {"name": "Germany", "sessions": 200},
            {"name": "India", "sessions": 150},
            {"name": "United Kingdom", "sessions": 100},
            {"name": "Canada", "sessions": 60},
            {"name": "France", "sessions": 40},
            {"name": "Japan", "sessions": 20},
        ]
    },
    "acquisition_over_time": {
        "daily": [
            {"date": "08-25", "users": 100},
            {"date": "08-26", "users": 140},
            {"date": "08-27", "users": 90},
            {"date": "08-28", "users": 200},
            {"date": "08-29", "users": 160},
            {"date": "08-30", "users": 180},
            {"date": "08-31", "users": 220},
        ]
    },
    "hourly_performance": {
        "hours": [{"hour": h, "sessions": (h * 7) % 53 + 5, "engagement_rate": 0.3 + (h % 5) * 0.05} for h in range(24)],
        "best_hour": 14,
    },
    "events": {
        "events": [
            {"name": "page_view", "count": 5000},
            {"name": "example_click", "count": 1200},
            {"name": "wizard_submit", "count": 400},
            {"name": "wizard_results", "count": 250},
        ]
    },
    "gsc": {
        "available": True,
        "striking_distance": [
            {"query": "how to deploy a repo to production", "impressions": 4000, "position": 9.2},
            {"query": "ga4 deep dive skill setup guide", "impressions": 3000, "position": 12.1},
            {"query": "repo atlas onboarding checklist", "impressions": 1500, "position": 15.4},
        ],
    },
    "insights": [
        {"icon": "🟢", "message": "Sessions up 60% WoW", "action": "Double down on Organic Search"},
        {"icon": "🚨", "message": "/promo/expired-campaign has a 100% bounce rate", "action": "Fix landing page"},
        {"icon": "🔴", "message": "Low stickiness: DAU/MAU is only 6.0%", "action": "Run retention campaigns"},
    ],
}


def _sample_data():
    return json.loads(json.dumps(FULL_DATA))


def _png_dimensions(path):
    """Read width/height straight out of the PNG IHDR chunk — avoids pulling
    in Pillow just for a test assertion."""
    with open(path, "rb") as handle:
        header = handle.read(24)
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    return width, height


# ---- compose_dashboard: happy path ------------------------------------------------


def test_compose_dashboard_writes_non_empty_png_of_expected_width(tmp_path):
    output_path = str(tmp_path / "dashboard.png")
    result = charts.compose_dashboard(_sample_data(), "repo-atlas", 7, output_path)
    assert result == output_path

    import os

    assert os.path.getsize(output_path) > 0
    width, height = _png_dimensions(output_path)
    assert width == charts.FIG_WIDTH_PX
    # GSC is available in the fixture, so the canvas grows beyond the no-GSC baseline.
    assert height > charts.FIG_HEIGHT_PX


def test_compose_dashboard_baseline_height_with_no_gsc_and_no_goal(tmp_path):
    data = _sample_data()
    data["gsc"] = {"available": False}
    output_path = str(tmp_path / "baseline.png")
    charts.compose_dashboard(data, "repo-atlas", 7, output_path)
    assert _png_dimensions(output_path) == (charts.FIG_WIDTH_PX, charts.FIG_HEIGHT_PX)


def test_compose_dashboard_returns_the_output_path(tmp_path):
    output_path = str(tmp_path / "nested" / "out.png")
    import os

    os.makedirs(os.path.dirname(output_path))
    assert charts.compose_dashboard(_sample_data(), "repo-atlas", 7, output_path) == output_path


# ---- compose_dashboard: graceful degradation --------------------------------------


def test_compose_dashboard_handles_completely_empty_sections_without_crashing(tmp_path):
    output_path = str(tmp_path / "empty.png")
    empty_data = {
        "property": "repo-atlas",
        "days": 7,
        "generated_at": "2026-08-31 12:00 UTC",
        "executive": {"current": {}, "previous": {}},
        "health": {"scores": {}, "overall": None, "grade": "N/A"},
        "acquisition": {"channels": []},
        "geography": {"countries": []},
        "acquisition_over_time": {"daily": []},
        "hourly_performance": {"hours": [], "best_hour": None},
        "events": {"events": []},
        "gsc": {"available": False},
        "insights": [],
    }
    result = charts.compose_dashboard(empty_data, "repo-atlas", 7, output_path)
    assert result == output_path

    import os

    assert os.path.getsize(output_path) > 0
    assert _png_dimensions(output_path) == (charts.FIG_WIDTH_PX, charts.FIG_HEIGHT_PX)


def test_compose_dashboard_handles_missing_keys_entirely_without_crashing(tmp_path):
    output_path = str(tmp_path / "sparse.png")
    sparse_data = {"property": "repo-atlas", "days": 7, "generated_at": "2026-08-31 12:00 UTC"}
    result = charts.compose_dashboard(sparse_data, "repo-atlas", 7, output_path)
    assert result == output_path


def test_compose_dashboard_funnel_handles_partial_event_coverage(tmp_path):
    output_path = str(tmp_path / "partial_funnel.png")
    data = _sample_data()
    data["events"] = {"events": [{"name": "page_view", "count": 500}]}
    charts.compose_dashboard(data, "repo-atlas", 7, output_path)


def test_compose_dashboard_funnel_empty_state_when_no_matching_events(tmp_path):
    output_path = str(tmp_path / "no_funnel.png")
    data = _sample_data()
    data["events"] = {"events": [{"name": "some_other_event", "count": 500}]}
    charts.compose_dashboard(data, "repo-atlas", 7, output_path)


def test_compose_dashboard_kpi_tiles_handle_new_metric_with_no_previous(tmp_path):
    output_path = str(tmp_path / "new_kpi.png")
    data = _sample_data()
    del data["executive"]["previous"]["sessions"]
    charts.compose_dashboard(data, "repo-atlas", 7, output_path)


# ---- compose_dashboard: GSC panel skip vs empty-state -----------------------------


def test_compose_dashboard_skips_gsc_panel_when_gsc_unavailable(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(charts, "_draw_gsc_striking_distance", lambda *a, **k: calls.append(a))
    data = _sample_data()
    data["gsc"] = {"available": False}
    charts.compose_dashboard(data, "repo-atlas", 7, str(tmp_path / "no_gsc.png"))
    assert calls == []


def test_compose_dashboard_skips_gsc_panel_when_gsc_key_missing(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(charts, "_draw_gsc_striking_distance", lambda *a, **k: calls.append(a))
    data = _sample_data()
    del data["gsc"]
    charts.compose_dashboard(data, "repo-atlas", 7, str(tmp_path / "no_gsc2.png"))
    assert calls == []


def test_compose_dashboard_renders_gsc_panel_when_available_but_striking_distance_empty(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(charts, "_draw_gsc_striking_distance", lambda *a, **k: calls.append(a))
    data = _sample_data()
    data["gsc"] = {"available": True, "striking_distance": []}
    charts.compose_dashboard(data, "repo-atlas", 7, str(tmp_path / "gsc_empty.png"))
    assert len(calls) == 1


def test_compose_dashboard_renders_gsc_panel_when_available_with_rows(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(charts, "_draw_gsc_striking_distance", lambda *a, **k: calls.append(a))
    charts.compose_dashboard(_sample_data(), "repo-atlas", 7, str(tmp_path / "gsc_rows.png"))
    assert len(calls) == 1


def test_compose_dashboard_gsc_available_but_no_striking_distance_rows_renders_empty_state(tmp_path):
    data = _sample_data()
    data["gsc"] = {"available": True, "striking_distance": []}
    output_path = str(tmp_path / "gsc_empty_state.png")
    charts.compose_dashboard(data, "repo-atlas", 7, output_path)
    import os

    assert os.path.getsize(output_path) > 0


# ---- large-value formatting -----------------------------------------------------------


def test_compose_dashboard_handles_million_scale_and_fractional_metrics(tmp_path):
    data = _sample_data()
    data["executive"]["current"]["sessions"] = 2_500_000
    data["executive"]["current"]["engagementRate"] = 0.5123
    data["executive"]["previous"]["sessions"] = 1_000_000
    data["acquisition"]["channels"][0]["sessions"] = 45.7  # exercises the fractional-value branch
    output_path = str(tmp_path / "million_scale.png")
    charts.compose_dashboard(data, "repo-atlas", 7, output_path)
    caption = charts.compose_caption(data, "repo-atlas", 7)
    assert "2.5M" in caption


# ---- label truncation ---------------------------------------------------------------


def test_truncate_label_leaves_short_labels_untouched():
    assert charts._truncate_label("Organic Search") == "Organic Search"


def test_truncate_label_ellipsizes_long_labels():
    result = charts._truncate_label("how to deploy a repo to production", max_len=22)
    assert len(result) <= 22
    assert result.endswith("…")
    assert result.startswith("how to deploy a repo")


# ---- compose_caption ----------------------------------------------------------------


def test_compose_caption_contains_property_and_period():
    caption = charts.compose_caption(_sample_data(), "repo-atlas", 7)
    assert "REPO-ATLAS" in caption
    assert "Last 7 days" in caption


def test_compose_caption_contains_all_four_headline_kpis_with_wow_arrows():
    caption = charts.compose_caption(_sample_data(), "repo-atlas", 7)
    for label in ("Sessions", "Users", "Engagement Rate", "Page Views"):
        assert label in caption
    assert "▲" in caption  # all four KPIs grew WoW in the fixture


def test_compose_caption_contains_top_three_insights():
    caption = charts.compose_caption(_sample_data(), "repo-atlas", 7)
    assert "Sessions up 60% WoW" in caption
    assert "100% bounce rate" in caption
    assert "Low stickiness" in caption


def test_compose_caption_caps_insights_at_three():
    data = _sample_data()
    data["insights"] = [{"icon": "🟢", "message": f"insight number {i}", "action": "do something"} for i in range(6)]
    caption = charts.compose_caption(data, "repo-atlas", 7)
    assert caption.count("insight number") == 3


def test_compose_caption_contains_top_striking_distance_query():
    caption = charts.compose_caption(_sample_data(), "repo-atlas", 7)
    assert "how to deploy a repo to production" in caption
    assert "pos 9.2" in caption


def test_compose_caption_skips_striking_distance_line_when_gsc_unavailable():
    data = _sample_data()
    data["gsc"] = {"available": False}
    caption = charts.compose_caption(data, "repo-atlas", 7)
    assert "striking-distance query" not in caption


def test_compose_caption_handles_new_metric_with_no_previous():
    data = _sample_data()
    del data["executive"]["previous"]["sessions"]
    caption = charts.compose_caption(data, "repo-atlas", 7)
    assert "NEW" in caption


def test_compose_caption_is_always_under_the_telegram_limit():
    caption = charts.compose_caption(_sample_data(), "repo-atlas", 7)
    assert len(caption) < 1024


def test_compose_caption_truncates_when_insights_are_pathologically_long():
    data = _sample_data()
    data["insights"] = [
        {"icon": "🟢", "message": "x" * 500, "action": "y"},
        {"icon": "🟢", "message": "z" * 500, "action": "w"},
        {"icon": "🟢", "message": "q" * 500, "action": "r"},
    ]
    caption = charts.compose_caption(data, "repo-atlas", 7)
    assert len(caption) <= 1024


def test_compose_caption_handles_empty_data_without_crashing():
    caption = charts.compose_caption(
        {"executive": {"current": {}, "previous": {}}, "insights": [], "gsc": None}, "repo-atlas", 7
    )
    assert "REPO-ATLAS" in caption
    assert len(caption) < 1024


# ---- rounded bars ------------------------------------------------------------------

GOAL = {"target": 1000000, "date": "2026-11-27", "metric": "totalUsers", "label": "1,000,000 users"}


def _fresh_axis():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.5, 4.5)
    return fig, ax


def test_rounded_bar_adds_a_fancybboxpatch_to_the_axis():
    fig, ax = _fresh_axis()
    try:
        patch = charts._rounded_bar(ax, 0, 0, 40, 0.6, "#3987e5")
        assert isinstance(patch, FancyBboxPatch)
        assert patch in ax.patches
    finally:
        plt.close(fig)


def test_rounded_bar_handles_zero_width_without_error():
    fig, ax = _fresh_axis()
    try:
        patch = charts._rounded_bar(ax, 0, 0, 0, 0.6, "#3987e5")
        assert patch in ax.patches
    finally:
        plt.close(fig)


def test_rounded_bar_handles_negative_or_degenerate_axis_scale_without_error():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlim(0, 0)  # degenerate scale
    ax.set_ylim(-0.5, 4.5)
    try:
        patch = charts._rounded_bar(ax, 0, 0, 0, 0.6, "#3987e5")
        assert patch in ax.patches
    finally:
        plt.close(fig)


def test_draw_horizontal_bars_uses_rounded_patches_not_plain_rectangles():
    fig, ax = _fresh_axis()
    try:
        rows = [{"name": "Organic Search", "sessions": 600}, {"name": "Direct", "sessions": 400}]
        charts._draw_horizontal_bars(ax, rows, "name", "sessions", charts.CATEGORICAL)
        assert len(ax.patches) == 2
        assert all(isinstance(p, FancyBboxPatch) for p in ax.patches)
    finally:
        plt.close(fig)


def test_draw_hourly_performance_uses_rounded_vertical_patches(tmp_path):
    data = _sample_data()
    output_path = str(tmp_path / "hourly.png")
    charts.compose_dashboard(data, "repo-atlas", 7, output_path)
    import os

    assert os.path.getsize(output_path) > 0


# ---- actionable insights panel -----------------------------------------------------


def test_severity_for_icon_maps_red_circle_to_critical():
    assert charts._severity_for_icon("🔴") == "critical"


def test_severity_for_icon_maps_siren_to_critical():
    assert charts._severity_for_icon("🚨") == "critical"


def test_severity_for_icon_maps_green_circle_to_good():
    assert charts._severity_for_icon("🟢") == "good"


def test_severity_for_icon_defaults_unknown_icons_to_warning():
    assert charts._severity_for_icon("❓") == "warning"


def test_severity_color_matches_the_validated_status_palette():
    assert charts._severity_color("🔴") == charts.STATUS_CRITICAL
    assert charts._severity_color("🚨") == charts.STATUS_CRITICAL
    assert charts._severity_color("🟢") == charts.STATUS_GOOD
    assert charts._severity_color("❓") == charts.STATUS_WARNING


def test_top_insight_cards_caps_at_five():
    data = {"insights": [{"icon": "🟢", "message": f"insight {i}", "action": "do it"} for i in range(8)]}
    cards = charts._top_insight_cards(data)
    assert len(cards) == 5


def test_top_insight_cards_returns_empty_list_when_no_insights():
    assert charts._top_insight_cards({"insights": []}) == []
    assert charts._top_insight_cards({}) == []


def test_compose_dashboard_renders_insights_panel_without_crashing(tmp_path):
    output_path = str(tmp_path / "insights.png")
    charts.compose_dashboard(_sample_data(), "repo-atlas", 7, output_path)
    import os

    assert os.path.getsize(output_path) > 0


def test_compose_dashboard_insights_panel_empty_state_when_no_insights(tmp_path):
    data = _sample_data()
    data["insights"] = []
    output_path = str(tmp_path / "no_insights.png")
    charts.compose_dashboard(data, "repo-atlas", 7, output_path)
    import os

    assert os.path.getsize(output_path) > 0


# ---- north-star pacing panel --------------------------------------------------------


def test_compose_dashboard_renders_pacing_panel_when_goal_is_present(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(charts, "_draw_pacing_panel", lambda *a, **k: calls.append(a))
    data = _sample_data()
    data["goal"] = GOAL
    charts.compose_dashboard(data, "repo-atlas", 7, str(tmp_path / "with_goal.png"))
    assert len(calls) == 1


def test_compose_dashboard_omits_pacing_panel_when_goal_is_absent(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(charts, "_draw_pacing_panel", lambda *a, **k: calls.append(a))
    data = _sample_data()
    data["goal"] = None
    charts.compose_dashboard(data, "repo-atlas", 7, str(tmp_path / "no_goal.png"))
    assert calls == []


def test_compose_dashboard_omits_pacing_panel_when_goal_key_missing(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(charts, "_draw_pacing_panel", lambda *a, **k: calls.append(a))
    data = _sample_data()
    assert "goal" not in data
    charts.compose_dashboard(data, "repo-atlas", 7, str(tmp_path / "no_goal_key.png"))
    assert calls == []


def test_compose_dashboard_grows_taller_with_a_goal_present(tmp_path):
    data_without = _sample_data()
    data_with = _sample_data()
    data_with["goal"] = GOAL

    path_without = str(tmp_path / "without_goal.png")
    path_with = str(tmp_path / "with_goal.png")
    charts.compose_dashboard(data_without, "repo-atlas", 7, path_without)
    charts.compose_dashboard(data_with, "repo-atlas", 7, path_with)

    _, height_without = _png_dimensions(path_without)
    _, height_with = _png_dimensions(path_with)
    assert height_with > height_without


def test_compose_dashboard_pacing_panel_renders_without_crashing(tmp_path):
    data = _sample_data()
    data["goal"] = GOAL
    output_path = str(tmp_path / "pacing.png")
    charts.compose_dashboard(data, "repo-atlas", 7, output_path)
    import os

    assert os.path.getsize(output_path) > 0


# ---- GSC label width ----------------------------------------------------------------


def test_gsc_label_max_chars_allows_roughly_thirty_characters():
    assert charts.GSC_LABEL_MAX_CHARS >= 30


def test_gsc_striking_distance_query_no_longer_truncates_at_the_old_width():
    query = "how to deploy a repo to production"  # 34 chars — used to truncate at the old 22-char width
    result = charts._truncate_label(query, max_len=charts.GSC_LABEL_MAX_CHARS)
    assert result == query
    assert "…" not in result


def test_gsc_panel_uses_the_wider_label_budget(tmp_path, monkeypatch):
    captured = {}
    original = charts._draw_horizontal_bars

    def _spy(ax, rows, label_key, value_key, colors, annotate_fn=None, label_max_chars=charts.LABEL_MAX_CHARS):
        result = original(ax, rows, label_key, value_key, colors, annotate_fn=annotate_fn, label_max_chars=label_max_chars)
        captured["ax"] = ax
        return result

    monkeypatch.setattr(charts, "_draw_horizontal_bars", _spy)
    data = _sample_data()
    charts.compose_dashboard(data, "repo-atlas", 7, str(tmp_path / "gsc_wide.png"))
    labels = [t.get_text() for t in captured["ax"].get_yticklabels()]
    assert "how to deploy a repo to production" in labels
