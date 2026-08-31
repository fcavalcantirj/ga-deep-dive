from gadeepdive import northstar

BASE_DATA = {
    "days": 7,
    "generated_at": "2026-08-31 12:00 UTC",
    "executive": {
        "current": {"totalUsers": 100000},
        "previous": {"totalUsers": 93000},
    },
}

GOAL = {"target": 1000000, "date": "2026-11-27", "metric": "totalUsers", "label": "1,000,000 users"}


def test_compute_pacing_returns_none_when_goal_is_absent():
    assert northstar.compute_pacing(BASE_DATA, None) is None


def test_compute_pacing_returns_none_when_goal_is_empty_dict():
    assert northstar.compute_pacing(BASE_DATA, {}) is None


def test_compute_pacing_reports_current_total_from_the_goal_metric():
    pacing = northstar.compute_pacing(BASE_DATA, GOAL)
    assert pacing["current_total"] == 100000
    assert pacing["target"] == 1000000
    assert pacing["label"] == "1,000,000 users"


def test_compute_pacing_percent_of_target():
    pacing = northstar.compute_pacing(BASE_DATA, GOAL)
    assert pacing["percent"] == 10.0


def test_compute_pacing_days_left_counts_from_generated_at_to_goal_date():
    data = dict(BASE_DATA, generated_at="2026-11-20 09:00 UTC")
    pacing = northstar.compute_pacing(data, GOAL)
    assert pacing["days_left"] == 7


def test_compute_pacing_days_left_floors_at_zero_when_date_has_passed():
    data = dict(BASE_DATA, generated_at="2026-12-25 09:00 UTC")
    pacing = northstar.compute_pacing(data, GOAL)
    assert pacing["days_left"] == 0


def test_compute_pacing_current_rate_is_wow_delta_over_period_days():
    pacing = northstar.compute_pacing(BASE_DATA, GOAL)
    # (100000 - 93000) / 7 days
    assert round(pacing["current_rate"], 2) == 1000.0


def test_compute_pacing_required_rate_is_remaining_over_days_left():
    data = dict(BASE_DATA, generated_at="2026-10-28 09:00 UTC")  # 30 days left
    pacing = northstar.compute_pacing(data, GOAL)
    assert pacing["days_left"] == 30
    assert round(pacing["required_rate"], 2) == round((1000000 - 100000) / 30, 2)


def test_compute_pacing_ahead_when_current_rate_meets_required_rate():
    data = {
        "days": 7,
        "generated_at": "2026-11-20 09:00 UTC",  # 7 days left
        "executive": {"current": {"totalUsers": 999995}, "previous": {"totalUsers": 999990}},
    }
    pacing = northstar.compute_pacing(data, GOAL)
    # required: 5/7 per day ~ 0.71; current: 5/7 per day ~ 0.71 -> ahead (>=)
    assert pacing["ahead"] is True


def test_compute_pacing_behind_when_current_rate_below_required_rate():
    data = {
        "days": 7,
        "generated_at": "2026-11-20 09:00 UTC",  # 7 days left
        "executive": {"current": {"totalUsers": 100000}, "previous": {"totalUsers": 99999}},
    }
    pacing = northstar.compute_pacing(data, GOAL)
    assert pacing["ahead"] is False


def test_compute_pacing_treats_target_already_reached_as_ahead():
    data = {
        "days": 7,
        "generated_at": "2026-08-31 12:00 UTC",
        "executive": {"current": {"totalUsers": 1200000}, "previous": {"totalUsers": 1100000}},
    }
    pacing = northstar.compute_pacing(data, GOAL)
    assert pacing["current_total"] == 1200000
    assert pacing["required_rate"] == 0
    assert pacing["ahead"] is True


def test_compute_pacing_handles_missing_executive_section_without_crashing():
    pacing = northstar.compute_pacing({"days": 7, "generated_at": "2026-08-31 12:00 UTC"}, GOAL)
    assert pacing["current_total"] == 0
    assert pacing["percent"] == 0.0
