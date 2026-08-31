from gadeepdive import fetch_activity

from .fixtures import FakeBackend

EVENT_ROWS = [
    {"eventName": "repo_starred", "eventCount": 500, "eventCountPerUser": 1.2},
    {"eventName": "commit_pushed", "eventCount": 900, "eventCountPerUser": 3.4},
]

DOW_ROWS = [
    {"dayOfWeek": "1", "sessions": 100, "engagedSessions": 60},
    {"dayOfWeek": "0", "sessions": 40, "engagedSessions": 10},
]

DAILY_ROWS = [
    {"date": "20260827", "sessions": 30},
    {"date": "20260825", "sessions": 10},
    {"date": "20260826", "sessions": 40},
]


def _backend(**dim_rows):
    return FakeBackend(dim_rows=dim_rows)


# ---- events ------------------------------------------------------------------------


def test_events_sorted_desc_by_count():
    backend = _backend(events=EVENT_ROWS)
    result = fetch_activity.events(backend, days=7)
    names = [e["name"] for e in result["events"]]
    assert names == ["commit_pushed", "repo_starred"]


def test_events_carries_per_user_rate():
    backend = _backend(events=EVENT_ROWS)
    result = fetch_activity.events(backend, days=7)
    repo_starred = next(e for e in result["events"] if e["name"] == "repo_starred")
    assert repo_starred["per_user"] == 1.2


def test_events_empty_backend_returns_empty_list():
    backend = _backend()
    result = fetch_activity.events(backend, days=7)
    assert result == {"events": []}


# ---- time patterns --------------------------------------------------------------------


def test_day_of_week_ordered_sunday_first_with_names_and_engaged_pct():
    backend = _backend(time_day_of_week=DOW_ROWS)
    result = fetch_activity.time_patterns(backend, days=7)
    days = result["day_of_week"]
    assert [d["day_name"] for d in days] == ["Sunday", "Monday"]
    assert days[1]["engaged_pct"] == 0.6


def test_weekday_name_mapping():
    assert fetch_activity._weekday_name("0") == "Sunday"
    assert fetch_activity._weekday_name("6") == "Saturday"
    assert fetch_activity._weekday_name("bogus") == "bogus"


def test_daily_sparkline_rows_sorted_chronologically_with_formatted_date():
    backend = _backend(time_daily=DAILY_ROWS)
    result = fetch_activity.time_patterns(backend, days=7)
    daily = result["daily"]
    assert [d["date"] for d in daily] == ["08-25", "08-26", "08-27"]
    assert daily[0]["sessions"] == 10


def test_format_ga4_date():
    assert fetch_activity._format_ga4_date("20260825") == "08-25"
    assert fetch_activity._format_ga4_date("not-a-date") == "not-a-date"


def test_daily_always_queries_last_7_days_regardless_of_report_period():
    backend = _backend(time_daily=DAILY_ROWS)
    fetch_activity.time_patterns(backend, days=30)
    daily_call = next(c for c in backend.calls if c[4].get("row_key") == "time_daily")
    assert daily_call[3] == 7


def test_time_patterns_empty_backend_returns_empty_lists():
    backend = _backend()
    result = fetch_activity.time_patterns(backend, days=7)
    assert result == {"day_of_week": [], "daily": []}
