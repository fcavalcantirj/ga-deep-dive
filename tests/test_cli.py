import json

import pytest

from gadeepdive import cli

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
