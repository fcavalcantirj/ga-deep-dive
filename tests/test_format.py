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


# ---- telegram phone-width helpers --------------------------------------------------


def test_truncate_leaves_short_text_untouched():
    assert fmt.truncate("repo-atlas", 20) == "repo-atlas"


def test_truncate_cuts_and_marks_long_text():
    result = fmt.truncate("firmware-release-pipeline", 10)
    assert len(result) == 10
    assert result.endswith("…")
    assert result == "firmware-…"


def test_truncate_width_one_has_no_room_for_ellipsis():
    assert fmt.truncate("firmware", 1) == "f"


def test_fixed_cell_pads_short_text_left_aligned():
    assert fmt.fixed_cell("repo", 8, "l") == "repo    "


def test_fixed_cell_pads_short_text_right_aligned():
    assert fmt.fixed_cell("42", 8, "r") == "      42"


def test_fixed_cell_truncates_text_wider_than_the_field():
    assert fmt.fixed_cell("firmware-release-pipeline", 8, "l") == "firmwar…"


def test_fixed_row_joins_cells_with_single_space_and_is_width_bound():
    row = fmt.fixed_row([("commit_pushed", 14, "l"), ("900", 7, "r"), ("3.40", 6, "r")])
    assert len(row) <= 14 + 1 + 7 + 1 + 6
    assert "commit_pushed" in row
    assert row.split()[-1] == "3.40"


def test_fixed_row_never_exceeds_width_even_with_a_very_long_field():
    row = fmt.fixed_row([("this-endpoint-name-is-way-too-long-for-a-phone-screen", 10, "l"), ("5", 4, "r")])
    assert len(row) <= 10 + 1 + 4


def test_code_block_wraps_lines_in_triple_backtick_fence():
    result = fmt.code_block(["repo    12", "board     4"])
    assert result.startswith("```\n")
    assert result.endswith("\n```")
    assert "repo    12" in result


# ---- telegram_delta -----------------------------------------------------------------


def test_telegram_delta_green_for_growth():
    assert fmt.telegram_delta(150, 100) == "🟢+50%"


def test_telegram_delta_red_for_decline():
    assert fmt.telegram_delta(50, 100) == "🔴-50%"


def test_telegram_delta_green_for_exactly_zero_change():
    assert fmt.telegram_delta(100, 100) == "🟢+0%"


def test_telegram_delta_new_when_no_previous_and_positive_current():
    assert fmt.telegram_delta(100, None) == "NEW"
    assert fmt.telegram_delta(100, 0) == "NEW"


def test_telegram_delta_dash_when_no_previous_and_zero_current():
    assert fmt.telegram_delta(0, None) == "—"


def test_telegram_delta_reverse_flips_polarity_for_bounce_rate_style_metrics():
    # Bounce rate dropping (good) reads green even though the raw number fell.
    assert fmt.telegram_delta(50, 100, reverse=True) == "🟢+50%"
    # Bounce rate rising (bad) reads red.
    assert fmt.telegram_delta(150, 100, reverse=True) == "🔴-50%"


# ---- section_header_telegram ---------------------------------------------------------


def test_section_header_telegram_is_bold_markdown_with_emoji():
    assert fmt.section_header_telegram("EXECUTIVE SUMMARY", "📊") == "\n**📊 EXECUTIVE SUMMARY**"
