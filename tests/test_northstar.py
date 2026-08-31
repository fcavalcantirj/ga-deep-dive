from gadeepdive import northstar

BASE_DATA = {
    "days": 7,
    "generated_at": "2026-08-31 12:00 UTC",
    "goal_totals": {"current_total": 100000, "current_rate": 1000.0},
}

GOAL = {"target": 1000000, "date": "2026-11-27", "metric": "totalUsers", "label": "1,000,000 users"}


def test_compute_pacing_returns_none_when_goal_is_absent():
    assert northstar.compute_pacing(BASE_DATA, None) is None


def test_compute_pacing_returns_none_when_goal_is_empty_dict():
    assert northstar.compute_pacing(BASE_DATA, {}) is None


def test_compute_pacing_reports_current_total_and_rate_from_goal_totals():
    pacing = northstar.compute_pacing(BASE_DATA, GOAL)
    assert pacing["current_total"] == 100000
    assert pacing["current_rate"] == 1000.0
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


def test_compute_pacing_required_rate_is_remaining_over_days_left():
    data = dict(BASE_DATA, generated_at="2026-10-28 09:00 UTC")  # 30 days left
    pacing = northstar.compute_pacing(data, GOAL)
    assert pacing["days_left"] == 30
    assert round(pacing["required_rate"], 2) == round((1000000 - 100000) / 30, 2)


def test_compute_pacing_ahead_when_current_rate_meets_required_rate():
    data = {
        "generated_at": "2026-11-20 09:00 UTC",  # 7 days left
        "goal_totals": {"current_total": 999995, "current_rate": 5 / 7},
    }
    pacing = northstar.compute_pacing(data, GOAL)
    # required: 5/7 per day; current: 5/7 per day -> ahead (>=)
    assert pacing["ahead"] is True


def test_compute_pacing_behind_when_current_rate_below_required_rate():
    data = {
        "generated_at": "2026-11-20 09:00 UTC",  # 7 days left
        "goal_totals": {"current_total": 100000, "current_rate": 1.0},
    }
    pacing = northstar.compute_pacing(data, GOAL)
    assert pacing["ahead"] is False


def test_compute_pacing_treats_target_already_reached_as_ahead():
    data = {
        "generated_at": "2026-08-31 12:00 UTC",
        "goal_totals": {"current_total": 1200000, "current_rate": 5000.0},
    }
    pacing = northstar.compute_pacing(data, GOAL)
    assert pacing["current_total"] == 1200000
    assert pacing["required_rate"] == 0
    assert pacing["ahead"] is True


def test_compute_pacing_degrades_to_zero_when_goal_totals_missing():
    """Goal present but `data["goal_totals"]` wasn't fetched (or fetch came
    back empty) — pacing renders at zero instead of crashing."""
    pacing = northstar.compute_pacing({"generated_at": "2026-08-31 12:00 UTC"}, GOAL)
    assert pacing["current_total"] == 0
    assert pacing["current_rate"] == 0
    assert pacing["percent"] == 0.0


def test_compute_pacing_realistic_esp_atlas_snapshot_is_far_behind():
    """esp-atlas's real numbers as of 2026-08-31: 153 lifetime users, ~5/day,
    88 days left to 1,000,000 — nowhere close to on pace."""
    data = {
        "generated_at": "2026-08-31 12:00 UTC",  # 88 days left to 2026-11-27
        "goal_totals": {"current_total": 153, "current_rate": 5.0},
    }
    pacing = northstar.compute_pacing(data, GOAL)
    assert pacing["days_left"] == 88
    assert round(pacing["percent"], 2) == round(153 / 1000000 * 100, 2)
    assert round(pacing["required_rate"], 2) == round((1000000 - 153) / 88, 2)
    assert pacing["current_rate"] == 5.0
    assert pacing["ahead"] is False
