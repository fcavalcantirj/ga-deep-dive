from gadeepdive import fetch_part2

from .fixtures import FakeBackend


def _backend(**dim_rows):
    return FakeBackend(dim_rows=dim_rows)


# ---- scroll depth ----------------------------------------------------------------

SCROLL_DIST_ROWS = [
    {"percentScrolled": "10", "eventCount": 500},
    {"percentScrolled": "25", "eventCount": 400},
    {"percentScrolled": "50", "eventCount": 300},
    {"percentScrolled": "75", "eventCount": 200},
    {"percentScrolled": "90", "eventCount": 100},
    {"percentScrolled": "100", "eventCount": 50},
]

SCROLL_PAGE_ROWS = [
    {"pagePath": "/docs/api-reference", "percentScrolled": "90", "eventCount": 80, "screenPageViews": 100},
    {"pagePath": "/docs/api-reference", "percentScrolled": "100", "eventCount": 20, "screenPageViews": 100},
    {"pagePath": "/blog/release-notes", "percentScrolled": "90", "eventCount": 10, "screenPageViews": 200},
]


def test_scroll_depth_buckets_have_counts_and_share():
    backend = _backend(scroll_distribution=SCROLL_DIST_ROWS)
    result = fetch_part2.scroll_depth(backend, days=7)
    distribution = result["distribution"]
    assert [d["depth"] for d in distribution] == ["10", "25", "50", "75", "90", "100"]
    assert distribution[0]["count"] == 500
    assert round(distribution[0]["share"], 2) == round(500 / 1550, 2)
    assert result["total_events"] == 1550


def test_scroll_depth_missing_bucket_defaults_to_zero():
    backend = _backend(scroll_distribution=[{"percentScrolled": "10", "eventCount": 100}])
    result = fetch_part2.scroll_depth(backend, days=7)
    by_depth = {d["depth"]: d["count"] for d in result["distribution"]}
    assert by_depth["100"] == 0


def test_scroll_depth_no_data_has_zero_total_events():
    backend = _backend()
    result = fetch_part2.scroll_depth(backend, days=7)
    assert result["total_events"] == 0
    assert result["top_pages"] == []


def test_scroll_depth_per_page_completion_rate_is_share_of_pageviews_reaching_90():
    backend = _backend(scroll_by_page=SCROLL_PAGE_ROWS)
    result = fetch_part2.scroll_depth(backend, days=7)
    top_pages = {p["path"]: p["completion_rate"] for p in result["top_pages"]}
    assert round(top_pages["/docs/api-reference"], 2) == 1.0  # (80+20)/100
    assert round(top_pages["/blog/release-notes"], 2) == 0.05  # 10/200


def test_scroll_depth_top_pages_sorted_by_completion_rate_desc():
    backend = _backend(scroll_by_page=SCROLL_PAGE_ROWS)
    result = fetch_part2.scroll_depth(backend, days=7)
    rates = [p["completion_rate"] for p in result["top_pages"]]
    assert rates == sorted(rates, reverse=True)


# ---- user flow entry points -------------------------------------------------------

ENTRY_ROWS = [
    {"landingPagePlusQueryString": "/pricing?ref=hn", "sessions": 80, "bounceRate": 0.35},
    {"landingPagePlusQueryString": "/", "sessions": 300, "bounceRate": 0.5},
]


def test_user_flow_entries_have_sessions_and_bounce():
    backend = _backend(flow_entries=ENTRY_ROWS)
    result = fetch_part2.user_flow(backend, days=7)
    entries = result["entries"]
    assert entries[0]["path"] == "/"
    assert entries[0]["entries"] == 300
    assert entries[0]["bounce_pct"] == 0.5
    assert entries[1]["path"] == "/pricing?ref=hn"


def test_user_flow_empty_backend_returns_empty_entries():
    backend = _backend()
    result = fetch_part2.user_flow(backend, days=7)
    assert result == {"entries": []}


# ---- audiences ----------------------------------------------------------------

AUDIENCE_ROWS = [
    {"audienceName": "Repeat Committers", "activeUsers": 120, "sessions": 300, "engagementRate": 0.55},
    {"audienceName": "(not set)", "activeUsers": 10, "sessions": 10, "engagementRate": 0.1},
    {"audienceName": "All Users", "activeUsers": 500, "sessions": 900, "engagementRate": 0.3},
]


def test_audiences_excludes_not_set_and_all_users():
    backend = _backend(audiences=AUDIENCE_ROWS)
    result = fetch_part2.audiences(backend, days=7)
    names = [a["name"] for a in result["audiences"]]
    assert names == ["Repeat Committers"]


def test_audiences_empty_backend_returns_empty_list():
    backend = _backend()
    result = fetch_part2.audiences(backend, days=7)
    assert result == {"audiences": []}


# ---- hourly performance -------------------------------------------------------

HOURLY_ROWS = [
    {"hour": "9", "sessions": 100, "engagedSessions": 40, "engagementRate": 0.4, "averageSessionDuration": 60.0},
    {"hour": "21", "sessions": 50, "engagedSessions": 45, "engagementRate": 0.9, "averageSessionDuration": 200.0},
    {"hour": "3", "sessions": 5, "engagedSessions": 1, "engagementRate": 0.2, "averageSessionDuration": 10.0},
]


def test_hourly_performance_sorted_by_hour_ascending():
    backend = _backend(hourly=HOURLY_ROWS)
    result = fetch_part2.hourly_performance(backend, days=7)
    hours = [h["hour"] for h in result["hours"]]
    assert hours == [3, 9, 21]


def test_hourly_performance_best_hour_is_highest_engagement_rate():
    backend = _backend(hourly=HOURLY_ROWS)
    result = fetch_part2.hourly_performance(backend, days=7)
    assert result["best_hour"] == 21


def test_hourly_performance_empty_backend_has_no_best_hour():
    backend = _backend()
    result = fetch_part2.hourly_performance(backend, days=7)
    assert result == {"hours": [], "best_hour": None}


# ---- acquisition over time -----------------------------------------------------

ACQ_TIME_ROWS = [
    {"date": "20260825", "activeUsers": 40},
    {"date": "20260826", "activeUsers": 120},
    {"date": "20260827", "activeUsers": 10},
]


def test_acquisition_over_time_sorted_descending_by_users():
    backend = _backend(acq_over_time=ACQ_TIME_ROWS)
    result = fetch_part2.acquisition_over_time(backend, days=7)
    users = [d["users"] for d in result["daily"]]
    assert users == [120, 40, 10]


def test_acquisition_over_time_formats_ga4_date():
    backend = _backend(acq_over_time=ACQ_TIME_ROWS)
    result = fetch_part2.acquisition_over_time(backend, days=7)
    dates = {d["date"] for d in result["daily"]}
    assert "08-26" in dates


def test_acquisition_over_time_leaves_non_ga4_date_unchanged():
    backend = _backend(acq_over_time=[{"date": "yesterday", "activeUsers": 5}])
    result = fetch_part2.acquisition_over_time(backend, days=7)
    assert result["daily"][0]["date"] == "yesterday"


# ---- mobile devices -------------------------------------------------------------

MOBILE_ROWS = [
    {"mobileDeviceModel": "Pixel 9", "sessions": 40},
    {"mobileDeviceModel": "(not set)", "sessions": 200},
    {"mobileDeviceModel": "iPhone 16", "sessions": 90},
]


def test_mobile_devices_excludes_not_set_and_sorts_desc():
    backend = _backend(mobile_devices=MOBILE_ROWS)
    result = fetch_part2.mobile_devices(backend, days=7)
    models = [m["model"] for m in result["models"]]
    assert models == ["iPhone 16", "Pixel 9"]


def test_mobile_devices_empty_backend_returns_empty_list():
    backend = _backend()
    result = fetch_part2.mobile_devices(backend, days=7)
    assert result == {"models": []}


# ---- blank labels -------------------------------------------------------------------


def test_scroll_depth_blank_page_path_gets_direct_entry_label():
    backend = _backend(scroll_by_page=[{"pagePath": "", "percentScrolled": "90", "eventCount": 10, "screenPageViews": 50}])
    result = fetch_part2.scroll_depth(backend, days=7)
    paths = [p["path"] for p in result["top_pages"]]
    assert "(direct entry)" in paths


def test_user_flow_blank_landing_page_gets_direct_entry_label():
    backend = _backend(flow_entries=[{"landingPagePlusQueryString": "", "sessions": 50, "bounceRate": 0.4}])
    result = fetch_part2.user_flow(backend, days=7)
    assert result["entries"][0]["path"] == "(direct entry)"


def test_mobile_devices_blank_model_gets_unknown_device_label():
    backend = _backend(mobile_devices=[{"mobileDeviceModel": "", "sessions": 5}])
    result = fetch_part2.mobile_devices(backend, days=7)
    assert result["models"][0]["model"] == "(unknown device)"
