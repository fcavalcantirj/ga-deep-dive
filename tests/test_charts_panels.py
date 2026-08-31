import os

import matplotlib.pyplot as plt

from gadeepdive import charts

from .chart_fixtures import BASE_EXEC_METRICS, _all_texts, _panel_fig, _sample_data, _tile_delta

# ---- PART 1 parity panels ------------------------------------------------------------


def test_compose_dashboard_renders_full_part1_parity_data_without_crashing(tmp_path):
    output_path = str(tmp_path / "part1_full.png")
    charts.compose_dashboard(_sample_data(), "repo-atlas", 7, output_path)
    assert os.path.getsize(output_path) > 0


# ---- live now badge -------------------------------------------------------------------


def test_draw_live_now_shows_active_user_count():
    fig, cell = _panel_fig()
    try:
        charts._draw_live_now(fig, cell, {"active_users": 42})
        texts = _all_texts(fig)
        assert any("LIVE NOW" in t and "42" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_live_now_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_live_now(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No realtime data" in t for t in texts)
    finally:
        plt.close(fig)


# ---- KPI tiles: all nine executive-summary metrics -------------------------------------


def test_draw_kpi_tiles_includes_all_nine_metrics():
    executive = {
        "current": {**BASE_EXEC_METRICS},
        "previous": {k: v * 0.8 for k, v in BASE_EXEC_METRICS.items()},
    }
    fig, cell = _panel_fig()
    try:
        charts._draw_kpi_tiles(fig, cell, executive)
        texts = _all_texts(fig)
        for label in ["Sessions", "Users", "New Users", "Engaged Sessions", "Engagement Rate",
                      "Bounce Rate", "Avg Duration", "Pages/Session", "Page Views"]:
            assert label.upper() in texts, f"missing tile label {label}"
    finally:
        plt.close(fig)


def test_draw_kpi_tiles_bounce_rate_decrease_is_treated_as_good():
    executive = {
        "current": {**BASE_EXEC_METRICS, "bounceRate": 0.30},
        "previous": {**BASE_EXEC_METRICS, "bounceRate": 0.50},
    }
    fig, cell = _panel_fig()
    try:
        charts._draw_kpi_tiles(fig, cell, executive)
        delta = _tile_delta(fig, "BOUNCE RATE")
        assert delta is not None
        assert delta.get_color() == charts.STATUS_GOOD
        assert "▼" in delta.get_text()
    finally:
        plt.close(fig)


def test_draw_kpi_tiles_bounce_rate_increase_is_treated_as_bad():
    executive = {
        "current": {**BASE_EXEC_METRICS, "bounceRate": 0.60},
        "previous": {**BASE_EXEC_METRICS, "bounceRate": 0.40},
    }
    fig, cell = _panel_fig()
    try:
        charts._draw_kpi_tiles(fig, cell, executive)
        delta = _tile_delta(fig, "BOUNCE RATE")
        assert delta is not None
        assert delta.get_color() == charts.STATUS_CRITICAL
        assert "▲" in delta.get_text()
    finally:
        plt.close(fig)


def test_draw_kpi_tiles_sessions_increase_is_treated_as_good():
    executive = {
        "current": {**BASE_EXEC_METRICS, "sessions": 1200},
        "previous": {**BASE_EXEC_METRICS, "sessions": 1000},
    }
    fig, cell = _panel_fig()
    try:
        charts._draw_kpi_tiles(fig, cell, executive)
        delta = _tile_delta(fig, "SESSIONS")
        assert delta.get_color() == charts.STATUS_GOOD
        assert "▲" in delta.get_text()
    finally:
        plt.close(fig)


def test_draw_kpi_tiles_degrades_to_zero_values_and_em_dash_deltas_when_missing():
    """The KPI grid always shows all nine metric tiles (fixed spec, not
    data-gated) — its degrade-on-missing-data behavior is zero values and
    em-dash deltas rather than swapping the whole panel for an empty-state
    label."""
    fig, cell = _panel_fig()
    try:
        charts._draw_kpi_tiles(fig, cell, {})
        texts = _all_texts(fig)
        assert "SESSIONS" in texts
        assert "BOUNCE RATE" in texts
        assert "—" in texts
    finally:
        plt.close(fig)


# ---- user activity: DAU/WAU/MAU + stickiness --------------------------------------------


def test_draw_user_activity_shows_dau_wau_mau_and_stickiness_chips():
    activity = {"active1DayUsers": 120, "active7DayUsers": 500, "active28DayUsers": 1800,
                "dauPerWau": 0.24, "dauPerMau": 0.067}
    fig, cell = _panel_fig()
    try:
        charts._draw_user_activity(fig, cell, activity)
        texts = _all_texts(fig)
        for label in ["DAU", "WAU", "MAU", "DAU/WAU", "DAU/MAU"]:
            assert label.upper() in texts
    finally:
        plt.close(fig)


def test_draw_user_activity_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_user_activity(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No user activity data available" in t for t in texts)
    finally:
        plt.close(fig)


# ---- acquisition detail: top referrer + first-touch attribution -------------------------


def test_draw_acquisition_detail_renders_top_referrer_and_attribution_table():
    acquisition = {
        "top_referrer": {"source_medium": "news.ycombinator.com / referral", "sessions": 210},
        "first_touch": [{"source": "google", "medium": "organic", "sessions": 600, "share": 0.38}],
    }
    fig, cell = _panel_fig()
    try:
        charts._draw_acquisition_detail(fig, cell, acquisition)
        texts = _all_texts(fig)
        assert any("news.ycombinator.com" in t for t in texts)
        assert any("google" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_acquisition_detail_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_acquisition_detail(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No attribution data available" in t for t in texts)
    finally:
        plt.close(fig)


# ---- geography languages -----------------------------------------------------------------


def test_draw_geography_languages_renders_bars():
    geography = {"languages": [{"name": "en-us", "sessions": 900, "share": 0.57}]}
    fig, cell = _panel_fig()
    try:
        charts._draw_geography_languages(fig, cell, geography)
        texts = _all_texts(fig)
        assert any("en-us" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_geography_languages_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_geography_languages(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No language data available" in t for t in texts)
    finally:
        plt.close(fig)


# ---- content: section bars, trending up, problem pages -----------------------------------


def test_draw_content_bars_renders_sections():
    content = {"sections": [{"section": "/docs", "views": 2200, "engagement_pct": 0.61}]}
    fig, cell = _panel_fig()
    try:
        charts._draw_content_bars(fig, cell, content)
        texts = _all_texts(fig)
        assert any("/docs" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_content_bars_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_content_bars(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No content data available" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_content_lists_renders_trending_and_problem_pages():
    content = {
        "trending_up": [{"path": "/docs/quickstart", "pct_change": 0.85}],
        "problem_pages": [{"path": "/promo/expired-campaign", "bounce_pct": 1.0}],
    }
    fig, cell = _panel_fig()
    try:
        charts._draw_content_lists(fig, cell, content)
        texts = _all_texts(fig)
        assert any("/docs/quickstart" in t for t in texts)
        assert any("/promo/expired-campaign" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_content_lists_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_content_lists(fig, cell, {})
        texts = _all_texts(fig)
        assert any("no WoW gainers" in t for t in texts)
        assert any("none" in t for t in texts)
    finally:
        plt.close(fig)


# ---- user segments: new vs returning + device breakdown -----------------------------------


def test_draw_user_segments_renders_new_vs_returning_and_device_bars():
    segments = {
        "new_vs_returning": [{"segment": "New", "sessions": 900, "engagement_pct": 0.48}],
        "by_device": [{"device": "mobile", "sessions": 900, "share": 0.57}],
    }
    fig, cell = _panel_fig()
    try:
        charts._draw_user_segments(fig, cell, segments)
        texts = _all_texts(fig)
        assert any("New" in t for t in texts)
        assert any("mobile" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_user_segments_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_user_segments(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No segment data available" in t for t in texts)
        assert any("No device data available" in t for t in texts)
    finally:
        plt.close(fig)


# ---- events: full bar list ------------------------------------------------------------------


def test_draw_events_full_renders_top_events_with_per_user_annotation():
    events_data = {"events": [{"name": "page_view", "count": 5000, "per_user": 5.2}]}
    fig, cell = _panel_fig()
    try:
        charts._draw_events_full(fig, cell, events_data)
        texts = _all_texts(fig)
        assert any("page_view" in t for t in texts)
        assert any("/user" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_events_full_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_events_full(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No event data available" in t for t in texts)
    finally:
        plt.close(fig)


# ---- time patterns: day of week --------------------------------------------------------------


def test_draw_day_of_week_renders_bars():
    time_patterns = {"day_of_week": [{"day_name": "Monday", "sessions": 300, "engaged_pct": 0.5}]}
    fig, cell = _panel_fig()
    try:
        charts._draw_day_of_week(fig, cell, time_patterns)
        texts = _all_texts(fig)
        assert any("Monday" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_day_of_week_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_day_of_week(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No day-of-week data available" in t for t in texts)
    finally:
        plt.close(fig)


# ---- technology: browsers + resolutions --------------------------------------------------------


def test_draw_technology_renders_browsers_and_resolutions():
    technology = {
        "browsers": [{"name": "Chrome", "sessions": 1100, "engaged_pct": 0.55}],
        "resolutions": [{"resolution": "1920x1080", "sessions": 500}],
    }
    fig, cell = _panel_fig()
    try:
        charts._draw_technology(fig, cell, technology)
        texts = _all_texts(fig)
        assert any("Chrome" in t for t in texts)
        assert any("1920x1080" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_technology_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_technology(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No browser data available" in t for t in texts)
        assert any("No resolution data available" in t for t in texts)
    finally:
        plt.close(fig)


# ---- PART 2 parity panels ------------------------------------------------------------


def test_compose_dashboard_renders_full_part2_and_gsc_data_without_crashing(tmp_path):
    output_path = str(tmp_path / "part2_full.png")
    charts.compose_dashboard(_sample_data(), "repo-atlas", 7, output_path)
    assert os.path.getsize(output_path) > 0


# ---- scroll depth: distribution + page completion --------------------------------------


def test_draw_scroll_depth_renders_distribution_and_page_completion_bars():
    scroll_depth = {
        "distribution": [{"depth": "25", "count": 3200, "share": 0.80}],
        "total_events": 4000,
        "top_pages": [{"path": "/docs/quickstart", "completion_rate": 0.62}],
    }
    fig, cell = _panel_fig()
    try:
        charts._draw_scroll_depth(fig, cell, scroll_depth)
        texts = _all_texts(fig)
        assert any("25%" in t for t in texts)
        assert any("/docs/quickstart" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_scroll_depth_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_scroll_depth(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No scroll data available" in t for t in texts)
        assert any("No page completion data available" in t for t in texts)
    finally:
        plt.close(fig)


# ---- user flow: entry points ------------------------------------------------------------


def test_draw_entry_points_renders_bars_with_bounce_pct():
    user_flow = {"entries": [{"path": "/docs/quickstart", "entries": 900, "bounce_pct": 0.22}]}
    fig, cell = _panel_fig()
    try:
        charts._draw_entry_points(fig, cell, user_flow)
        texts = _all_texts(fig)
        assert any("/docs/quickstart" in t for t in texts)
        assert any("bounce" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_entry_points_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_entry_points(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No entry point data available" in t for t in texts)
    finally:
        plt.close(fig)


# ---- GA4 audiences ------------------------------------------------------------------------


def test_draw_audiences_renders_bars():
    audiences = {"audiences": [{"name": "Power Users", "users": 400, "sessions": 900, "engagement_pct": 0.72}]}
    fig, cell = _panel_fig()
    try:
        charts._draw_audiences(fig, cell, audiences)
        texts = _all_texts(fig)
        assert any("Power Users" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_audiences_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_audiences(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No custom audiences configured" in t for t in texts)
    finally:
        plt.close(fig)


# ---- mobile devices ------------------------------------------------------------------------


def test_draw_mobile_devices_renders_bars():
    mobile_devices = {"models": [{"model": "iPhone 15", "sessions": 500}]}
    fig, cell = _panel_fig()
    try:
        charts._draw_mobile_devices(fig, cell, mobile_devices)
        texts = _all_texts(fig)
        assert any("iPhone 15" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_mobile_devices_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_mobile_devices(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No mobile device data available" in t for t in texts)
    finally:
        plt.close(fig)


# ---- Search Console: totals chips + top queries table --------------------------------------


def test_draw_gsc_totals_renders_stat_chips():
    gsc = {"totals": {"clicks": 5200, "impressions": 84000, "ctr": 0.062, "avg_position": 14.3}}
    fig, cell = _panel_fig()
    try:
        charts._draw_gsc_totals(fig, cell, gsc)
        texts = _all_texts(fig)
        for label in ["Clicks", "Impressions", "CTR", "Avg Position"]:
            assert label.upper() in texts, f"missing GSC totals chip {label}"
        assert any("5.2K" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_gsc_totals_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_gsc_totals(fig, cell, {})
        texts = _all_texts(fig)
        assert any("No Search Console totals available" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_gsc_top_queries_renders_table_rows():
    gsc = {"top_queries": [{"query": "ga deep dive skill", "clicks": 900, "impressions": 12000, "ctr": 0.075, "position": 6.2}]}
    fig, cell = _panel_fig()
    try:
        charts._draw_gsc_top_queries(fig, cell, gsc)
        texts = _all_texts(fig)
        assert any("ga deep dive skill" in t for t in texts)
    finally:
        plt.close(fig)


def test_draw_gsc_top_queries_empty_state_when_missing():
    fig, cell = _panel_fig()
    try:
        charts._draw_gsc_top_queries(fig, cell, {})
        texts = _all_texts(fig)
        assert any("no query data" in t for t in texts)
    finally:
        plt.close(fig)
