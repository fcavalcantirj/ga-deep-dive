from gadeepdive import insights

# ---- dominant channel ---------------------------------------------------------------


def test_dominant_channel_fires_above_60_percent_share():
    data = {"acquisition": {"channels": [{"name": "Organic Search", "share": 0.75}]}}
    result = insights.compute(data)
    assert any("Organic Search" in i["message"] and "Diversify" in i["action"] for i in result)


def test_dominant_channel_silent_below_threshold():
    data = {"acquisition": {"channels": [{"name": "Organic Search", "share": 0.4}]}}
    result = insights.compute(data)
    assert not any("Diversify" in i["action"] for i in result)


def test_dominant_channel_silent_when_no_channels():
    assert insights.compute({"acquisition": {"channels": []}}) == []


# ---- low stickiness -------------------------------------------------------------------


def test_low_stickiness_fires_below_threshold():
    data = {"activity": {"dauPerMau": 0.03}}
    result = insights.compute(data)
    assert any("stickiness" in i["message"].lower() for i in result)


def test_low_stickiness_silent_above_threshold():
    data = {"activity": {"dauPerMau": 0.2}}
    result = insights.compute(data)
    assert not any("stickiness" in i["message"].lower() for i in result)


def test_low_stickiness_silent_when_missing():
    assert insights.compute({"activity": {}}) == []


# ---- problem pages ----------------------------------------------------------------------


def test_problem_page_insight_fires_with_worst_page():
    data = {
        "content": {
            "problem_pages": [
                {"path": "/promo/expired-campaign", "sessions": 20, "bounce_pct": 1.0},
                {"path": "/blog/broken-redirect", "sessions": 5, "bounce_pct": 0.97},
            ]
        }
    }
    result = insights.compute(data)
    matches = [i for i in result if i["icon"] == "🚨"]
    assert len(matches) == 1
    assert "/promo/expired-campaign" in matches[0]["message"]
    assert "2 pages affected" in matches[0]["message"]


def test_problem_page_insight_silent_when_none():
    assert insights.compute({"content": {"problem_pages": []}}) == []


# ---- strong WoW growth -----------------------------------------------------------------


def test_strong_growth_fires_above_threshold_with_channel_recommendation():
    data = {
        "health": {"scores": {"Growth": 90}},
        "executive": {"current": {"sessions": 200}, "previous": {"sessions": 100}},
        "acquisition": {"channels": [{"name": "Organic Search", "share": 0.5}]},
    }
    result = insights.compute(data)
    growth_insights = [i for i in result if "Sessions up" in i["message"]]
    assert len(growth_insights) == 1
    assert "100%" in growth_insights[0]["message"]
    assert "Organic Search" in growth_insights[0]["action"]


def test_strong_growth_silent_below_threshold():
    data = {"health": {"scores": {"Growth": 50}}, "executive": {}, "acquisition": {}}
    assert insights.compute(data) == []


# ---- top geography ----------------------------------------------------------------------


def test_top_geo_fires_for_high_quality_country():
    data = {"geography": {"countries": [{"name": "United States", "stars": 5}, {"name": "Germany", "stars": 1}]}}
    result = insights.compute(data)
    geo_insights = [i for i in result if "localization" in i["action"]]
    assert len(geo_insights) == 1
    assert "United States" in geo_insights[0]["message"]


def test_top_geo_silent_when_best_below_4_stars():
    data = {"geography": {"countries": [{"name": "Germany", "stars": 3}]}}
    result = insights.compute(data)
    assert not any("localization" in i["action"] for i in result)


def test_top_geo_silent_when_no_countries():
    assert insights.compute({"geography": {"countries": []}}) == []


# ---- combined ---------------------------------------------------------------------------


def test_compute_with_empty_data_returns_empty_list():
    assert insights.compute({}) == []


def test_compute_returns_multiple_insights_in_rule_order():
    data = {
        "acquisition": {"channels": [{"name": "Organic Search", "share": 0.9}]},
        "activity": {"dauPerMau": 0.02},
        "content": {"problem_pages": [{"path": "/x", "sessions": 1, "bounce_pct": 1.0}]},
        "health": {"scores": {"Growth": 95}},
        "executive": {"current": {"sessions": 300}, "previous": {"sessions": 100}},
        "geography": {"countries": [{"name": "Japan", "stars": 5}]},
    }
    result = insights.compute(data)
    assert len(result) == 5
    assert [i["icon"] for i in result] == ["🔴", "🔴", "🚨", "🟢", "🟢"]
