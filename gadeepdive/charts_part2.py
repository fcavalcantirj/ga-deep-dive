"""PART 2 panels: scroll depth (distribution + page completion), user-flow
entry points, GA4 audiences, and mobile devices.
"""

from typing import Any, Dict

from .charts_base import (
    CATEGORICAL,
    _draw_horizontal_bars,
    _draw_split_panel,
    _empty_state,
    _fmt_num,
    _fmt_pct,
    _new_panel_axis,
    _sub_label,
)

TOP_PAGES_TOP_N = 5
ENTRY_POINTS_TOP_N = 8
AUDIENCES_TOP_N = 8
MOBILE_DEVICES_TOP_N = 8

# ---- panel: scroll depth (distribution + page completion) -------------------------


def _draw_scroll_depth(fig, cell, scroll_depth: Dict[str, Any]) -> None:
    scroll_depth = scroll_depth or {}
    distribution = scroll_depth.get("distribution") or []
    top_pages = (scroll_depth.get("top_pages") or [])[:TOP_PAGES_TOP_N]

    def _left(ax):
        _sub_label(ax, "Depth Distribution")
        if not scroll_depth.get("total_events") or not distribution:
            _empty_state(ax, "No scroll data available")
            return
        rows = [{"depth_label": f"{d.get('depth')}%", "count": d.get("count", 0), "share": d.get("share", 0)}
                for d in distribution]

        def _annotate(row, value):
            return f"{_fmt_num(value)} ({_fmt_pct(row.get('share', 0))})"

        _draw_horizontal_bars(ax, rows, "depth_label", "count", CATEGORICAL, annotate_fn=_annotate)

    def _right(ax):
        _sub_label(ax, "Page Completion")
        if not top_pages:
            _empty_state(ax, "No page completion data available")
            return

        def _annotate(row, value):
            return _fmt_pct(value)

        _draw_horizontal_bars(ax, top_pages, "path", "completion_rate", CATEGORICAL, annotate_fn=_annotate)

    _draw_split_panel(fig, cell, "Scroll Depth", _left, _right)


# ---- panel: user flow entry points -------------------------------------------------


def _draw_entry_points(fig, cell, user_flow: Dict[str, Any]) -> None:
    entries = ((user_flow or {}).get("entries") or [])[:ENTRY_POINTS_TOP_N]
    ax = _new_panel_axis(fig, cell, "User Flow — Entry Points")
    if not entries:
        _empty_state(ax, "No entry point data available")
        return

    def _annotate(row, value):
        return f"{_fmt_num(value)} ({_fmt_pct(row.get('bounce_pct', 0))} bounce)"

    _draw_horizontal_bars(ax, entries, "path", "entries", CATEGORICAL, annotate_fn=_annotate)


# ---- panel: GA4 audiences -----------------------------------------------------------


def _draw_audiences(fig, cell, audiences: Dict[str, Any]) -> None:
    audience_list = ((audiences or {}).get("audiences") or [])[:AUDIENCES_TOP_N]
    ax = _new_panel_axis(fig, cell, "GA4 Audiences")
    if not audience_list:
        _empty_state(ax, "No custom audiences configured")
        return

    def _annotate(row, value):
        return f"{_fmt_num(row.get('sessions', 0))} sess · {_fmt_pct(row.get('engagement_pct', 0))}"

    _draw_horizontal_bars(ax, audience_list, "name", "users", CATEGORICAL, annotate_fn=_annotate)


# ---- panel: mobile devices -----------------------------------------------------------


def _draw_mobile_devices(fig, cell, mobile_devices: Dict[str, Any]) -> None:
    models = ((mobile_devices or {}).get("models") or [])[:MOBILE_DEVICES_TOP_N]
    ax = _new_panel_axis(fig, cell, "Mobile Devices")
    if not models:
        _empty_state(ax, "No mobile device data available")
        return

    _draw_horizontal_bars(ax, models, "model", "sessions", CATEGORICAL)
