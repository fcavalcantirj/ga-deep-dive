from gadeepdive import fetch

from .fixtures import FakeBackend


# ---- realtime_active_users --------------------------------------------------


def test_realtime_active_users_returns_count_from_row():
    backend = FakeBackend(realtime_rows=[{"activeUsers": 3}])
    result = fetch.realtime_active_users(backend)
    assert result == {"active_users": 3}
    assert backend.calls == [("run_realtime", ["activeUsers"])]


def test_realtime_active_users_defaults_to_zero_when_no_rows():
    backend = FakeBackend(realtime_rows=[])
    result = fetch.realtime_active_users(backend)
    assert result == {"active_users": 0}


# ---- executive_summary -------------------------------------------------------


CURRENT_ROW = {
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
}

PREVIOUS_ROW = {
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
}


def test_executive_summary_splits_current_and_previous():
    backend = FakeBackend(exec_rows=[CURRENT_ROW, PREVIOUS_ROW])
    result = fetch.executive_summary(backend, days=7)
    assert result["current"]["sessions"] == 157
    assert result["previous"]["sessions"] == 48
    assert "dateRange" not in result["current"]
    assert "dateRange" not in result["previous"]


def test_executive_summary_requests_compare_previous_extra():
    backend = FakeBackend(exec_rows=[CURRENT_ROW, PREVIOUS_ROW])
    fetch.executive_summary(backend, days=7)
    call = backend.calls[0]
    assert call[0] == "run_report"
    assert call[3] == 7
    assert call[4] == {"compare_previous": True}
    assert set(call[2]) == {
        "sessions",
        "activeUsers",
        "newUsers",
        "engagedSessions",
        "engagementRate",
        "bounceRate",
        "averageSessionDuration",
        "screenPageViewsPerSession",
        "screenPageViews",
    }


def test_executive_summary_previous_is_empty_when_only_current_row_present():
    backend = FakeBackend(exec_rows=[CURRENT_ROW])
    result = fetch.executive_summary(backend, days=7)
    assert result["current"]["sessions"] == 157
    assert result["previous"] == {}


def test_executive_summary_both_empty_when_backend_returns_no_rows():
    backend = FakeBackend(exec_rows=[])
    result = fetch.executive_summary(backend, days=7)
    assert result == {"current": {}, "previous": {}}


# ---- user_activity ------------------------------------------------------------


def test_user_activity_returns_row_data():
    backend = FakeBackend(
        activity_row={
            "active1DayUsers": 12,
            "active7DayUsers": 60,
            "active28DayUsers": 200,
            "dauPerWau": 0.2,
            "dauPerMau": 0.06,
        }
    )
    result = fetch.user_activity(backend)
    assert result["active1DayUsers"] == 12
    assert result["active7DayUsers"] == 60
    assert result["active28DayUsers"] == 200
    assert result["dauPerWau"] == 0.2
    assert result["dauPerMau"] == 0.06


def test_user_activity_requests_expected_metrics():
    backend = FakeBackend(activity_row={"active1DayUsers": 1})
    fetch.user_activity(backend)
    call = backend.calls[0]
    assert set(call[2]) == {
        "active1DayUsers",
        "active7DayUsers",
        "active28DayUsers",
        "dauPerWau",
        "dauPerMau",
    }


def test_user_activity_returns_empty_dict_when_no_data():
    backend = FakeBackend(activity_row={})
    result = fetch.user_activity(backend)
    assert result == {}


# ---- user_activity — stickiness bug fix (R2) -----------------------------------


def test_user_activity_queries_single_day_not_a_date_range():
    """The R1 bug: GA4 sums per-date active-user metrics across a multi-day
    range when queried without a date dimension. The fix pins the query to
    exactly one day (yesterday) so no summing can occur."""
    backend = FakeBackend(activity_row={"active1DayUsers": 12})
    fetch.user_activity(backend)
    call = backend.calls[0]
    assert call[1] == []  # no date dimension
    assert call[3] == 1  # single day, never the report's --days period
    assert call[4] == {"date_ranges": [{"startDate": "yesterday", "endDate": "yesterday"}]}


def test_user_activity_ignores_report_period_days_argument():
    """user_activity takes no `days` argument at all — it is never a
    function of the report period, only ever "the last complete day"."""
    import inspect

    params = inspect.signature(fetch.user_activity).parameters
    assert "days" not in params


def test_user_activity_stickiness_never_exceeds_100_percent():
    # Realistic snapshot: DAU < WAU < MAU always holds for a single day.
    backend = FakeBackend(
        activity_row={
            "active1DayUsers": 40,
            "active7DayUsers": 220,
            "active28DayUsers": 850,
            "dauPerWau": 0.1818,
            "dauPerMau": 0.0471,
        }
    )
    result = fetch.user_activity(backend)
    assert result["dauPerWau"] * 100 <= 100
    assert result["dauPerMau"] * 100 <= 100
    # Guard the historical bug shape: a naive DAU/WAU or DAU/MAU sum-based
    # ratio derived from the snapshot must also stay sane once GA4 stops
    # summing across days.
    dau, wau, mau = result["active1DayUsers"], result["active7DayUsers"], result["active28DayUsers"]
    assert dau <= wau <= mau
