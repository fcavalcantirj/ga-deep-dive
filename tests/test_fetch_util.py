from gadeepdive import fetch_util


def test_blank_label_passes_through_non_blank_value():
    assert fetch_util.blank_label("Organic Search") == "Organic Search"


def test_blank_label_falls_back_on_empty_string():
    assert fetch_util.blank_label("") == "(not set)"


def test_blank_label_falls_back_on_none():
    assert fetch_util.blank_label(None) == "(not set)"


def test_blank_label_accepts_custom_fallback():
    assert fetch_util.blank_label("", "(direct entry)") == "(direct entry)"
    assert fetch_util.blank_label(None, "(unknown device)") == "(unknown device)"


def test_blank_label_leaves_the_literal_ga4_not_set_string_unchanged():
    # GA4 sometimes sends the literal string "(not set)" itself — blank_label
    # only substitutes for None/"", never rewrites an already-present value.
    assert fetch_util.blank_label("(not set)", "(direct entry)") == "(not set)"
