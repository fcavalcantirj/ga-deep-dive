import json
import os

import pytest

from gadeepdive import cli, delivery

from .fixtures import FakeBackend

EXEC_ROWS = [
    {
        "dateRange": "current",
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
    {
        "dateRange": "previous",
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
]

ACTIVITY_ROW = {
    "active1DayUsers": 12,
    "active7DayUsers": 60,
    "active28DayUsers": 200,
    "dauPerWau": 0.2,
    "dauPerMau": 0.06,
}


def _install_fake_backend(monkeypatch):
    fake = FakeBackend(realtime_rows=[{"activeUsers": 3}], exec_rows=EXEC_ROWS, activity_row=ACTIVITY_ROW)
    monkeypatch.setattr(cli, "_make_backend", lambda backend_name, prop: fake)
    return fake


# ---- unknown property ----------------------------------------------------------


def test_main_unknown_property_returns_error_exit_code(capsys):
    exit_code = cli.main(["not-a-real-property"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "not-a-real-property" in captured.err
    assert "esp-atlas" in captured.err  # lists registered names


# ---- default (full + telegram) --------------------------------------------------


def test_main_default_output_includes_full_and_telegram(monkeypatch, capsys):
    _install_fake_backend(monkeypatch)
    exit_code = cli.main(["esp-atlas"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "GA4 DEEP DIVE v3" in out
    assert "╔" in out  # full ANSI box present
    assert "TELEGRAM VARIANT" in out


def test_main_no_telegram_skips_telegram_variant(monkeypatch, capsys):
    _install_fake_backend(monkeypatch)
    exit_code = cli.main(["esp-atlas", "--no-telegram"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "GA4 DEEP DIVE v3" in out
    assert "TELEGRAM VARIANT" not in out


# ---- --json ----------------------------------------------------------------------


def test_main_json_emits_valid_json_shape(monkeypatch, capsys):
    _install_fake_backend(monkeypatch)
    exit_code = cli.main(["esp-atlas", "--json"])
    assert exit_code == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["property"] == "esp-atlas"
    assert payload["days"] == 7
    assert payload["live_now"] == {"active_users": 3}
    assert payload["executive_summary"]["current"]["sessions"] == 157
    assert payload["executive_summary"]["previous"]["sessions"] == 48
    assert payload["user_activity"]["active1DayUsers"] == 12
    assert "scores" in payload["health"]


def test_main_json_skips_ansi_art(monkeypatch, capsys):
    _install_fake_backend(monkeypatch)
    cli.main(["esp-atlas", "--json"])
    out = capsys.readouterr().out
    assert "╔" not in out
    assert "TELEGRAM VARIANT" not in out


# ---- --days ------------------------------------------------------------------------


def test_main_passes_days_through_to_backend_calls(monkeypatch, capsys):
    fake = _install_fake_backend(monkeypatch)
    cli.main(["esp-atlas", "--days", "30", "--json"])
    capsys.readouterr()
    # user_activity (point-in-time snapshot) and the time-patterns daily
    # sparkline (always the last 7 days) are intentionally exempt — neither
    # is a function of the report's --days period.
    exempt_row_keys = {"time_daily"}
    period_calls = [
        call
        for call in fake.calls
        if call[0] == "run_report" and "date_ranges" not in call[4] and call[4].get("row_key") not in exempt_row_keys
    ]
    days_seen = {call[3] for call in period_calls}
    assert days_seen == {30}


# ---- --backend ----------------------------------------------------------------------


def test_main_native_backend_raises_not_implemented():
    with pytest.raises(NotImplementedError, match="native"):
        cli.main(["esp-atlas", "--backend", "native", "--json"])


def test_run_exits_with_mains_return_code(monkeypatch):
    monkeypatch.setattr(cli, "main", lambda: 0)
    with pytest.raises(SystemExit) as excinfo:
        cli.run()
    assert excinfo.value.code == 0


def test_build_arg_parser_defaults():
    parser = cli.build_arg_parser()
    args = parser.parse_args(["esp-atlas"])
    assert args.days == 7
    assert args.backend == "composio"
    assert args.json is False
    assert args.no_gsc is False
    assert args.no_telegram is False
    assert args.deliver is None
    assert args.dashboard is None


# ---- --deliver telegram ------------------------------------------------------------


def test_main_deliver_telegram_happy_path_sends_dashboard_photo(monkeypatch, capsys):
    _install_fake_backend(monkeypatch)
    sent = []
    monkeypatch.setattr(delivery, "send_photo", lambda image_path, caption, **kw: sent.append((image_path, caption)))
    exit_code = cli.main(["esp-atlas", "--deliver", "telegram", "--json"])
    assert exit_code == 0
    assert len(sent) == 1
    image_path, caption = sent[0]
    assert image_path.endswith(".png")
    assert "ESP-ATLAS" in caption
    assert len(caption) < 1024
    captured = capsys.readouterr()
    assert "Delivered to telegram." in captured.err


def test_main_deliver_telegram_never_sends_the_old_text_wall(monkeypatch):
    _install_fake_backend(monkeypatch)
    sent = []
    monkeypatch.setattr(delivery, "send_photo", lambda image_path, caption, **kw: sent.append((image_path, caption)))
    cli.main(["esp-atlas", "--deliver", "telegram", "--json"])
    assert len(sent) == 1
    _, caption = sent[0]
    assert "GA4 DEEP DIVE v3" not in caption  # the old text-wall is not what gets delivered


def test_main_deliver_telegram_missing_env_exits_nonzero(monkeypatch, capsys):
    _install_fake_backend(monkeypatch)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_HOME_CHANNEL", raising=False)
    exit_code = cli.main(["esp-atlas", "--deliver", "telegram", "--json"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "TELEGRAM_BOT_TOKEN" in captured.err
    assert captured.out == ""  # never printed the report if delivery failed


# ---- --dashboard ----------------------------------------------------------------------


def test_main_dashboard_writes_png_without_delivering(monkeypatch, capsys, tmp_path):
    _install_fake_backend(monkeypatch)
    sent = []
    monkeypatch.setattr(delivery, "send_photo", lambda *a, **kw: sent.append((a, kw)))
    output_path = str(tmp_path / "out.png")

    exit_code = cli.main(["esp-atlas", "--dashboard", output_path, "--json"])

    assert exit_code == 0
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    assert sent == []  # --dashboard alone never delivers
    captured = capsys.readouterr()
    assert f"Dashboard written to {output_path}." in captured.err


def test_main_wires_the_registered_goal_into_the_dashboard_data(monkeypatch, tmp_path):
    _install_fake_backend(monkeypatch)
    seen = {}

    def _fake_compose_dashboard(data, property_name, days, output_path):
        seen["goal"] = data.get("goal")
        return output_path

    monkeypatch.setattr(cli.charts, "compose_dashboard", _fake_compose_dashboard)
    output_path = str(tmp_path / "out.png")

    cli.main(["esp-atlas", "--dashboard", output_path, "--json"])

    assert seen["goal"] == {
        "target": 1000000,
        "date": "2026-11-27",
        "metric": "totalUsers",
        "label": "1,000,000 users",
    }


def test_main_wires_none_goal_for_properties_without_one(monkeypatch, tmp_path):
    _install_fake_backend(monkeypatch)
    seen = {}

    def _fake_compose_dashboard(data, property_name, days, output_path):
        seen["goal"] = data.get("goal")
        return output_path

    monkeypatch.setattr(cli.charts, "compose_dashboard", _fake_compose_dashboard)
    output_path = str(tmp_path / "out.png")

    cli.main(["abecmed", "--dashboard", output_path, "--json"])

    assert seen["goal"] is None


def test_main_dashboard_and_deliver_together(monkeypatch, tmp_path):
    _install_fake_backend(monkeypatch)
    sent = []
    monkeypatch.setattr(delivery, "send_photo", lambda image_path, caption, **kw: sent.append((image_path, caption)))
    output_path = str(tmp_path / "out.png")

    exit_code = cli.main(["esp-atlas", "--dashboard", output_path, "--deliver", "telegram", "--json"])

    assert exit_code == 0
    assert os.path.exists(output_path)
    assert len(sent) == 1


def test_build_arg_parser_deliver_choices():
    parser = cli.build_arg_parser()
    args = parser.parse_args(["esp-atlas", "--deliver", "telegram"])
    assert args.deliver == "telegram"
    with pytest.raises(SystemExit):
        parser.parse_args(["esp-atlas", "--deliver", "carrier-pigeon"])


# ---- collect_report_data (integration of fetch+health) --------------------------------


def test_collect_report_data_wires_fetch_and_health(monkeypatch):
    fake = FakeBackend(realtime_rows=[{"activeUsers": 5}], exec_rows=EXEC_ROWS, activity_row=ACTIVITY_ROW)
    data = cli.collect_report_data(fake, "esp-atlas", 7)
    assert data["property"] == "esp-atlas"
    assert data["realtime"] == {"active_users": 5}
    assert data["executive"]["current"]["sessions"] == 157
    assert data["health"]["scores"]["Engagement"] == 32


# ---- full §1-12 integration (PART 1 complete) ------------------------------------------

DIM_ROWS_FULL = {
    "acq_channels": [{"sessionDefaultChannelGroup": "Organic Search", "sessions": 300, "engagedSessions": 210, "bounceRate": 0.3, "averageSessionDuration": 120.0}],
    "acq_source_medium": [{"sessionSourceMedium": "github.com / referral", "sessions": 45}],
    "acq_first_touch": [{"firstUserSourceMedium": "google / organic", "sessions": 250}],
    "geo_country": [{"country": "United States", "sessions": 400, "engagedSessions": 280, "engagementRate": 0.62}],
    "geo_language": [{"language": "en-us", "sessions": 350}],
    "content_pages": [{"pagePath": "/docs/api-reference", "screenPageViews": 500, "activeUsers": 300, "engagementRate": 0.6}],
    "content_trending": [
        {"pagePath": "/docs/api-reference", "dateRange": "current", "screenPageViews": 500},
        {"pagePath": "/docs/api-reference", "dateRange": "previous", "screenPageViews": 100},
    ],
    "content_landing": [{"landingPage": "/promo/expired-campaign", "sessions": 20, "bounceRate": 1.0}],
    "segments_new_returning": [{"newVsReturning": "new", "sessions": 300, "engagementRate": 0.4}],
    "segments_device": [{"deviceCategory": "mobile", "sessions": 200, "engagementRate": 0.35}],
    "events": [{"eventName": "commit_pushed", "eventCount": 900, "eventCountPerUser": 3.4}],
    "time_day_of_week": [{"dayOfWeek": "1", "sessions": 100, "engagedSessions": 60}],
    "time_daily": [{"date": "20260827", "sessions": 30}, {"date": "20260826", "sessions": 40}],
    "tech_browser": [{"browser": "Chrome", "sessions": 400, "engagedSessions": 280}],
    "tech_resolution": [{"screenResolution": "1920x1080", "sessions": 300}],
}


def _install_full_fake_backend(monkeypatch):
    fake = FakeBackend(
        realtime_rows=[{"activeUsers": 3}],
        exec_rows=EXEC_ROWS,
        activity_row=ACTIVITY_ROW,
        dim_rows=DIM_ROWS_FULL,
    )
    monkeypatch.setattr(cli, "_make_backend", lambda backend_name, prop: fake)
    return fake


def test_main_full_report_renders_all_part1_sections(monkeypatch, capsys):
    _install_full_fake_backend(monkeypatch)
    exit_code = cli.main(["esp-atlas", "--no-telegram"])
    assert exit_code == 0
    out = capsys.readouterr().out
    for header in (
        "EXECUTIVE SUMMARY",
        "HEALTH DASHBOARD",
        "ACQUISITION",
        "GEOGRAPHY",
        "CONTENT",
        "USER SEGMENTS",
        "EVENTS",
        "TIME PATTERNS",
        "TECHNOLOGY",
        "ACTIONABLE INSIGHTS",
    ):
        assert header in out, f"missing section: {header}"
    assert "Organic Search" in out
    assert "United States" in out
    assert "commit_pushed" in out
    assert "← PEAK" in out


def test_main_json_includes_all_part1_sections(monkeypatch, capsys):
    _install_full_fake_backend(monkeypatch)
    cli.main(["esp-atlas", "--json"])
    payload = json.loads(capsys.readouterr().out)
    for key in ("acquisition", "geography", "content", "user_segments", "events", "time_patterns", "technology", "insights"):
        assert key in payload
    assert payload["acquisition"]["channels"][0]["name"] == "Organic Search"


# ---- full §13-19 + GSC integration (PART 2 complete) ------------------------------------

DIM_ROWS_FULL_PART2 = {
    **DIM_ROWS_FULL,
    "scroll_distribution": [{"percentScrolled": "90", "eventCount": 80}, {"percentScrolled": "100", "eventCount": 20}],
    "scroll_by_page": [{"pagePath": "/docs/api-reference", "percentScrolled": "90", "eventCount": 80, "screenPageViews": 100}],
    "flow_entries": [{"landingPagePlusQueryString": "/", "sessions": 300, "bounceRate": 0.5}],
    "audiences": [{"audienceName": "Repeat Committers", "activeUsers": 120, "sessions": 300, "engagementRate": 0.55}],
    "hourly": [{"hour": "21", "sessions": 50, "engagedSessions": 45, "engagementRate": 0.9, "averageSessionDuration": 200.0}],
    "acq_over_time": [{"date": "20260826", "activeUsers": 120}],
    "mobile_devices": [{"mobileDeviceModel": "Pixel 9", "sessions": 40}],
}

GSC_ROWS_FULL = [{"query": "how to deploy a repo", "clicks": 40, "impressions": 400, "ctr": 0.1, "position": 3.2}]


def _install_full_fake_backend_with_gsc(monkeypatch, gsc_site="sc-domain:esp-atlas.com"):
    fake = FakeBackend(
        realtime_rows=[{"activeUsers": 3}],
        exec_rows=EXEC_ROWS,
        activity_row=ACTIVITY_ROW,
        dim_rows=DIM_ROWS_FULL_PART2,
        gsc_rows=GSC_ROWS_FULL,
        gsc_site=gsc_site,
    )
    monkeypatch.setattr(cli, "_make_backend", lambda backend_name, prop: fake)
    return fake


def test_main_full_report_renders_part_labels_and_part2_sections(monkeypatch, capsys):
    _install_full_fake_backend_with_gsc(monkeypatch)
    exit_code = cli.main(["esp-atlas", "--no-telegram"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "PART 1: EXECUTIVE SUMMARY (V3)" in out
    assert "PART 2: THE FULL MONTY (V4)" in out
    for header in (
        "SCROLL DEPTH",
        "USER FLOW",
        "GA4 AUDIENCES",
        "HOURLY PERFORMANCE",
        "ACQUISITION OVER TIME",
        "MOBILE DEVICES",
        "FULL MONTY COMPLETE",
    ):
        assert header in out, f"missing section: {header}"
    assert "← BEST" in out
    assert "Pixel 9" in out


def test_main_full_report_includes_gsc_section_by_default(monkeypatch, capsys):
    _install_full_fake_backend_with_gsc(monkeypatch)
    cli.main(["esp-atlas", "--no-telegram"])
    out = capsys.readouterr().out
    assert "SEARCH CONSOLE" in out
    assert "how to deploy a repo" in out


def test_main_no_gsc_suppresses_search_console_section(monkeypatch, capsys):
    _install_full_fake_backend_with_gsc(monkeypatch)
    cli.main(["esp-atlas", "--no-telegram", "--no-gsc"])
    out = capsys.readouterr().out
    assert "SEARCH CONSOLE" not in out


def test_main_gsc_no_site_configured_prints_graceful_message(monkeypatch, capsys):
    _install_full_fake_backend_with_gsc(monkeypatch, gsc_site=None)
    cli.main(["abecmed", "--no-telegram"])
    out = capsys.readouterr().out
    assert "No Search Console site configured for abecmed" in out


def test_main_telegram_variant_includes_part2_and_gsc(monkeypatch, capsys):
    _install_full_fake_backend_with_gsc(monkeypatch)
    cli.main(["esp-atlas"])
    out = capsys.readouterr().out
    telegram_variant = out[out.index("TELEGRAM VARIANT"):]
    assert "PART 2: THE FULL MONTY (V4)" in telegram_variant
    assert "SEARCH CONSOLE" in telegram_variant


def test_main_json_includes_part2_and_gsc(monkeypatch, capsys):
    _install_full_fake_backend_with_gsc(monkeypatch)
    cli.main(["esp-atlas", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert "part2" in payload
    assert payload["part2"]["mobile_devices"]["models"][0]["model"] == "Pixel 9"
    assert payload["gsc"]["available"] is True
    assert payload["gsc"]["top_queries"][0]["query"] == "how to deploy a repo"


def test_main_json_no_gsc_sets_gsc_null(monkeypatch, capsys):
    _install_full_fake_backend_with_gsc(monkeypatch)
    cli.main(["esp-atlas", "--json", "--no-gsc"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["gsc"] is None


# ---- section order (oracle checklist) ---------------------------------------------


def test_main_full_report_sections_appear_in_oracle_order(monkeypatch, capsys):
    _install_full_fake_backend_with_gsc(monkeypatch)
    cli.main(["esp-atlas", "--no-telegram"])
    out = capsys.readouterr().out
    ordered_markers = [
        "PART 1: EXECUTIVE SUMMARY (V3)",
        "📊 EXECUTIVE SUMMARY",
        "🏥 HEALTH DASHBOARD",
        "🚦 ACQUISITION",
        "🌍 GEOGRAPHY",
        "📄 CONTENT",
        "👤 USER SEGMENTS",
        "⚡ EVENTS",
        "🕐 TIME PATTERNS",
        "💻 TECHNOLOGY",
        "💡 ACTIONABLE INSIGHTS",
        "PART 2: THE FULL MONTY (V4)",
        "📜 SCROLL DEPTH",
        "🚪 USER FLOW",
        "🎯 GA4 AUDIENCES",
        "🕐 HOURLY PERFORMANCE",
        "📅 ACQUISITION OVER TIME",
        "📱 MOBILE DEVICES",
        "✅ FULL MONTY COMPLETE",
        "🌐 SEARCH CONSOLE",
    ]
    positions = [out.index(marker) for marker in ordered_markers]
    assert positions == sorted(positions)


# ---- top-N caps: full/telegram truncate, --json keeps the full set ----------------

MANY_COUNTRIES_ROWS = [{"country": f"Country {i}", "sessions": 100 - i, "engagedSessions": 50, "engagementRate": 0.5} for i in range(15)]


def test_main_geography_caps_display_but_json_keeps_full_set(monkeypatch, capsys):
    dim_rows = {**DIM_ROWS_FULL, "geo_country": MANY_COUNTRIES_ROWS}
    fake = FakeBackend(realtime_rows=[{"activeUsers": 3}], exec_rows=EXEC_ROWS, activity_row=ACTIVITY_ROW, dim_rows=dim_rows)
    monkeypatch.setattr(cli, "_make_backend", lambda backend_name, prop: fake)

    cli.main(["esp-atlas", "--no-telegram"])
    full_out = capsys.readouterr().out
    assert "Country 9" in full_out
    assert "Country 10" not in full_out

    cli.main(["esp-atlas", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["geography"]["countries"]) == 15
