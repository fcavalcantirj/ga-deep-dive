from gadeepdive import fetch_content

from .fixtures import FakeBackend

PAGE_ROWS = [
    {"pagePath": "/docs/api-reference", "screenPageViews": 500, "activeUsers": 300, "engagementRate": 0.6},
    {"pagePath": "/docs/quickstart", "screenPageViews": 200, "activeUsers": 150, "engagementRate": 0.4},
    {"pagePath": "/blog/how-we-scaled-postgres", "screenPageViews": 100, "activeUsers": 90, "engagementRate": 0.5},
]

TRENDING_COMPARE_ROWS = [
    {"pagePath": "/docs/api-reference", "dateRange": "current", "screenPageViews": 500},
    {"pagePath": "/docs/api-reference", "dateRange": "previous", "screenPageViews": 100},
    {"pagePath": "/blog/how-we-scaled-postgres", "dateRange": "current", "screenPageViews": 100},
    {"pagePath": "/blog/how-we-scaled-postgres", "dateRange": "previous", "screenPageViews": 90},
    {"pagePath": "/docs/quickstart", "dateRange": "current", "screenPageViews": 50},
    {"pagePath": "/docs/quickstart", "dateRange": "previous", "screenPageViews": 0},  # no baseline -> excluded
]

LANDING_ROWS = [
    {"landingPage": "/promo/expired-campaign", "sessions": 20, "bounceRate": 1.0},
    {"landingPage": "/docs/quickstart", "sessions": 200, "bounceRate": 0.3},
    {"landingPage": "/blog/broken-redirect", "sessions": 5, "bounceRate": 0.97},
]


def _backend(**dim_rows):
    return FakeBackend(dim_rows=dim_rows)


# ---- section grouping --------------------------------------------------------------


def test_content_groups_pages_by_first_path_segment():
    backend = _backend(content_pages=PAGE_ROWS)
    result = fetch_content.content(backend, days=7)
    sections = {s["section"]: s for s in result["sections"]}
    assert set(sections) == {"docs", "blog"}
    assert sections["docs"]["views"] == 700
    assert sections["docs"]["page_count"] == 2
    assert sections["blog"]["page_count"] == 1


def test_content_section_engagement_is_view_weighted():
    backend = _backend(content_pages=PAGE_ROWS)
    result = fetch_content.content(backend, days=7)
    docs = next(s for s in result["sections"] if s["section"] == "docs")
    expected = (500 * 0.6 + 200 * 0.4) / 700
    assert round(docs["engagement_pct"], 4) == round(expected, 4)


def test_content_sections_sorted_desc_by_views():
    backend = _backend(content_pages=PAGE_ROWS)
    result = fetch_content.content(backend, days=7)
    views = [s["views"] for s in result["sections"]]
    assert views == sorted(views, reverse=True)


def test_section_for_path_handles_root():
    assert fetch_content._section_for_path("/") == "(root)"
    assert fetch_content._section_for_path("") == "(root)"
    assert fetch_content._section_for_path("/docs/api-reference") == "docs"


# ---- trending up (WoW) --------------------------------------------------------------


def test_trending_up_only_includes_positive_wow_gainers_with_baseline():
    backend = _backend(content_trending=TRENDING_COMPARE_ROWS)
    result = fetch_content.content(backend, days=7)
    paths = [t["path"] for t in result["trending_up"]]
    assert "/docs/api-reference" in paths
    assert "/blog/how-we-scaled-postgres" in paths
    assert "/docs/quickstart" not in paths  # no previous baseline


def test_trending_up_sorted_desc_by_pct_change():
    backend = _backend(content_trending=TRENDING_COMPARE_ROWS)
    result = fetch_content.content(backend, days=7)
    top = result["trending_up"][0]
    assert top["path"] == "/docs/api-reference"
    assert round(top["pct_change"], 2) == 4.0  # 500 vs 100 -> +400%


def test_trending_up_uses_compare_previous_extra():
    backend = _backend(content_trending=TRENDING_COMPARE_ROWS)
    fetch_content.content(backend, days=7)
    trending_call = next(c for c in backend.calls if c[4].get("row_key") == "content_trending")
    assert trending_call[4]["compare_previous"] is True


# ---- problem pages --------------------------------------------------------------------


def test_problem_pages_filters_by_bounce_threshold():
    backend = _backend(content_landing=LANDING_ROWS)
    result = fetch_content.content(backend, days=7)
    paths = [p["path"] for p in result["problem_pages"]]
    assert "/promo/expired-campaign" in paths
    assert "/blog/broken-redirect" in paths
    assert "/docs/quickstart" not in paths


def test_problem_pages_sorted_desc_by_bounce():
    backend = _backend(content_landing=LANDING_ROWS)
    result = fetch_content.content(backend, days=7)
    bounces = [p["bounce_pct"] for p in result["problem_pages"]]
    assert bounces == sorted(bounces, reverse=True)


def test_content_empty_backend_returns_empty_sections():
    backend = _backend()
    result = fetch_content.content(backend, days=7)
    assert result == {"sections": [], "trending_up": [], "problem_pages": []}


# ---- blank labels -------------------------------------------------------------------


def test_problem_pages_blank_landing_page_gets_direct_entry_label():
    backend = _backend(content_landing=[{"landingPage": "", "sessions": 20, "bounceRate": 1.0}])
    result = fetch_content.content(backend, days=7)
    assert result["problem_pages"][0]["path"] == "(direct entry)"
