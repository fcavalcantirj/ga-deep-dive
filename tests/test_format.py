from gadeepdive import format as fmt

# ---- star_string ------------------------------------------------------------------


def test_star_string_renders_filled_and_empty_stars():
    assert fmt.star_string(3) == "★★★☆☆"
    assert fmt.star_string(5) == "★★★★★"
    assert fmt.star_string(0) == "☆☆☆☆☆"


def test_star_string_clamps_out_of_range():
    assert fmt.star_string(10) == "★★★★★"
    assert fmt.star_string(-1) == "☆☆☆☆☆"


# ---- sparkline_lines --------------------------------------------------------------


def test_sparkline_marks_peak_day():
    rows = [
        {"date": "2026-08-25", "sessions": 10},
        {"date": "2026-08-26", "sessions": 40},
        {"date": "2026-08-27", "sessions": 15},
    ]
    lines = fmt.sparkline_lines(rows, "date", "sessions")
    assert "← PEAK" in lines[1]
    assert "← PEAK" not in lines[0]
    assert "← PEAK" not in lines[2]


def test_sparkline_empty_rows_returns_empty_list():
    assert fmt.sparkline_lines([], "date", "sessions") == []


def test_sparkline_single_row_is_the_peak():
    rows = [{"date": "2026-08-25", "sessions": 5}]
    lines = fmt.sparkline_lines(rows, "date", "sessions")
    assert len(lines) == 1
    assert "← PEAK" in lines[0]
