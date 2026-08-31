from gadeepdive import health

# ---- engagement_score --------------------------------------------------------


def test_engagement_score_scales_engagement_rate_to_0_100():
    assert health.engagement_score({"engagementRate": 0.318}) == 32


def test_engagement_score_caps_at_100():
    assert health.engagement_score({"engagementRate": 1.4}) == 100


def test_engagement_score_defaults_to_zero_when_missing():
    assert health.engagement_score({}) == 0


# ---- growth_score -------------------------------------------------------------


def test_growth_score_positive_wow_deltas_score_above_50():
    current = {"sessions": 157, "activeUsers": 96, "newUsers": 40, "engagedSessions": 88}
    previous = {"sessions": 48, "activeUsers": 30, "newUsers": 12, "engagedSessions": 20}
    score = health.growth_score(current, previous)
    assert score > 50
    assert score <= 100


def test_growth_score_negative_wow_deltas_score_below_50():
    current = {"sessions": 30, "activeUsers": 20, "newUsers": 5, "engagedSessions": 10}
    previous = {"sessions": 157, "activeUsers": 96, "newUsers": 40, "engagedSessions": 88}
    score = health.growth_score(current, previous)
    assert score < 50


def test_growth_score_no_previous_data_with_current_activity_is_new_fallback():
    current = {"sessions": 157, "activeUsers": 96, "newUsers": 40, "engagedSessions": 88}
    assert health.growth_score(current, {}) == 75


def test_growth_score_no_previous_data_and_no_current_activity_is_neutral():
    assert health.growth_score({}, {}) == 50


def test_growth_score_clamped_to_0_100():
    current = {"sessions": 100000, "activeUsers": 1, "newUsers": 1, "engagedSessions": 1}
    previous = {"sessions": 1, "activeUsers": 1, "newUsers": 1, "engagedSessions": 1}
    assert health.growth_score(current, previous) == 100


# ---- retention_score -----------------------------------------------------------


def test_retention_score_from_dau_per_mau():
    # 20% dau/mau => 100 (v3 reference formula: dau_per_mau * 500)
    assert health.retention_score({"dauPerMau": 0.2}) == 100
    assert health.retention_score({"dauPerMau": 0.06}) == 30


def test_retention_score_falls_back_to_computing_from_dau_and_mau():
    assert health.retention_score({"active1DayUsers": 12, "active28DayUsers": 200}) == 30


def test_retention_score_zero_when_no_data():
    assert health.retention_score({}) == 0


def test_retention_score_caps_at_100():
    assert health.retention_score({"dauPerMau": 0.9}) == 100


# ---- content_score --------------------------------------------------------------


def test_content_score_blends_engagement_and_problem_ratio():
    content = {
        "sections": [{"engagement_pct": 0.6, "page_count": 5}, {"engagement_pct": 0.4, "page_count": 5}],
        "problem_pages": [{"path": "/x"}],
    }
    # avg_engagement=0.5, problem_ratio=1/10=0.1 -> (0.5*0.9 + 0.5*0.5)*100 = 70
    assert health.content_score(content) == 70


def test_content_score_neutral_when_no_sections():
    assert health.content_score({"sections": [], "problem_pages": []}) == 50
    assert health.content_score(None) == 50
    assert health.content_score({}) == 50


def test_content_score_clamps_at_0_and_100():
    content = {"sections": [{"engagement_pct": 1.0, "page_count": 1}], "problem_pages": []}
    assert health.content_score(content) == 100


# ---- mobile_score -----------------------------------------------------------------


def test_mobile_score_blends_share_and_engagement():
    segments = {"by_device": [{"device": "mobile", "share": 0.4, "engagement_pct": 0.6}]}
    # (0.5*0.4 + 0.5*0.6)*100 = 50
    assert health.mobile_score(segments) == 50


def test_mobile_score_neutral_when_no_mobile_row():
    assert health.mobile_score({"by_device": [{"device": "desktop", "share": 1.0, "engagement_pct": 0.5}]}) == 50
    assert health.mobile_score(None) == 50


def test_mobile_score_is_case_insensitive_for_device_name():
    segments = {"by_device": [{"device": "Mobile", "share": 1.0, "engagement_pct": 1.0}]}
    assert health.mobile_score(segments) == 100


# ---- geo_diversity_score ------------------------------------------------------------


def test_geo_diversity_score_lower_when_top_country_concentrated():
    concentrated = {"countries": [{"share": 0.9}]}
    diverse = {"countries": [{"share": 0.3}]}
    assert health.geo_diversity_score(concentrated) < health.geo_diversity_score(diverse)


def test_geo_diversity_score_neutral_when_no_countries():
    assert health.geo_diversity_score({"countries": []}) == 50
    assert health.geo_diversity_score(None) == 50


def test_geo_diversity_score_full_concentration_scores_zero():
    assert health.geo_diversity_score({"countries": [{"share": 1.0}]}) == 0


# ---- traffic_diversity_score ---------------------------------------------------------


def test_traffic_diversity_score_lower_when_top_channel_concentrated():
    concentrated = {"channels": [{"share": 0.95}]}
    diverse = {"channels": [{"share": 0.4}]}
    assert health.traffic_diversity_score(concentrated) < health.traffic_diversity_score(diverse)


def test_traffic_diversity_score_neutral_when_no_channels():
    assert health.traffic_diversity_score({"channels": []}) == 50
    assert health.traffic_diversity_score(None) == 50


def test_traffic_diversity_score_full_concentration_scores_zero():
    assert health.traffic_diversity_score({"channels": [{"share": 1.0}]}) == 0


# ---- grade_for -----------------------------------------------------------------


def test_grade_for_thresholds():
    assert health.grade_for(95) == "A+"
    assert health.grade_for(90) == "A+"
    assert health.grade_for(89) == "A"
    assert health.grade_for(80) == "A"
    assert health.grade_for(79) == "B"
    assert health.grade_for(65) == "B"
    assert health.grade_for(64) == "C"
    assert health.grade_for(50) == "C"
    assert health.grade_for(49) == "D"
    assert health.grade_for(0) == "D"


def test_grade_for_none_is_not_available():
    assert health.grade_for(None) == "N/A"


# ---- compute_dashboard -----------------------------------------------------------


def test_compute_dashboard_wires_real_scores_including_r2_sections():
    executive = {
        "current": {"sessions": 157, "activeUsers": 96, "newUsers": 40, "engagedSessions": 88, "engagementRate": 0.318},
        "previous": {"sessions": 48, "activeUsers": 30, "newUsers": 12, "engagedSessions": 20},
    }
    activity = {"active1DayUsers": 12, "active7DayUsers": 60, "active28DayUsers": 200, "dauPerMau": 0.06}
    acquisition = {"channels": [{"share": 0.5}]}
    geography = {"countries": [{"share": 0.5}]}
    content = {"sections": [{"engagement_pct": 0.4, "page_count": 10}], "problem_pages": []}
    segments = {"by_device": [{"device": "mobile", "share": 0.4, "engagement_pct": 0.5}]}

    dashboard = health.compute_dashboard(executive, activity, acquisition, geography, content, segments)

    assert dashboard["scores"]["Engagement"] == 32
    assert dashboard["scores"]["Retention"] == 30
    assert dashboard["scores"]["Growth"] > 50
    assert dashboard["scores"]["Content"] == 70
    assert dashboard["scores"]["Mobile"] == 45
    assert dashboard["scores"]["Geo Diversity"] == 50
    assert dashboard["scores"]["Traffic Diversity"] == 50


def test_compute_dashboard_defaults_r2_sections_to_neutral_when_omitted():
    executive = {"current": {"engagementRate": 0.5}, "previous": {}}
    activity = {"dauPerMau": 0.2}
    dashboard = health.compute_dashboard(executive, activity)
    assert dashboard["scores"]["Content"] == 50
    assert dashboard["scores"]["Mobile"] == 50
    assert dashboard["scores"]["Geo Diversity"] == 50
    assert dashboard["scores"]["Traffic Diversity"] == 50


def test_compute_dashboard_overall_averages_all_seven_scores():
    executive = {"current": {"engagementRate": 0.5}, "previous": {}}
    activity = {"dauPerMau": 0.2}
    dashboard = health.compute_dashboard(executive, activity)
    available = [v for v in dashboard["scores"].values() if v is not None]
    assert len(available) == 7
    expected_overall = round(sum(available) / len(available))
    assert dashboard["overall"] == expected_overall
    assert dashboard["grade"] == health.grade_for(expected_overall)


def test_compute_dashboard_overall_is_none_if_somehow_all_scores_missing(monkeypatch):
    for name in ("engagement_score", "growth_score", "retention_score", "content_score", "mobile_score", "geo_diversity_score", "traffic_diversity_score"):
        monkeypatch.setattr(health, name, lambda *a, **k: None)
    dashboard = health.compute_dashboard({"current": {}, "previous": {}}, {})
    assert dashboard["overall"] is None
    assert dashboard["grade"] == "N/A"
