"""Time-series and activity panels: daily users, hourly performance,
day-of-week, the event funnel, the full events bar list, and technology
(browsers + resolutions).
"""

from typing import Any, Dict

from .charts_base import (
    CATEGORICAL,
    GRID_MUTED,
    SEQUENTIAL_BLUES,
    STATUS_GOOD,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    _draw_horizontal_bars,
    _draw_split_panel,
    _empty_state,
    _fmt_num,
    _fmt_pct,
    _new_panel_axis,
    _rounded_hbars,
    _rounded_vbars,
    _sub_label,
)

FUNNEL_STEPS = ["page_view", "example_click", "wizard_submit", "wizard_results"]
EVENTS_TOP_N = 12
RESOLUTIONS_TOP_N = 5

# ---- panel: daily users (area + line) -------------------------------------------


def _draw_daily_users(fig, cell, acquisition_over_time: Dict[str, Any]) -> None:
    ax = _new_panel_axis(fig, cell, "Daily Users")
    daily = list((acquisition_over_time or {}).get("daily") or [])
    if not daily:
        _empty_state(ax, "No daily users data available")
        return

    daily_sorted = sorted(daily, key=lambda d: str(d.get("date", "")))[-8:]
    labels = [str(d.get("date", "")) for d in daily_sorted]
    values = [float(d.get("users", 0) or 0) for d in daily_sorted]
    x = list(range(len(values)))
    line_color = SEQUENTIAL_BLUES[2]

    ax.plot(x, values, color=line_color, linewidth=2, zorder=3)
    ax.fill_between(x, values, color=line_color, alpha=0.18, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=TEXT_SECONDARY, fontsize=8)
    ax.set_yticks([])
    ax.grid(axis="y", color=GRID_MUTED, linewidth=0.6, zorder=0)

    peak_idx = max(range(len(values)), key=lambda i: values[i])
    ax.scatter([x[peak_idx]], [values[peak_idx]], color=STATUS_GOOD, s=45, zorder=4)
    ax.annotate(
        f"Peak {_fmt_num(values[peak_idx])}", (x[peak_idx], values[peak_idx]),
        textcoords="offset points", xytext=(0, 10), ha="center",
        color=TEXT_PRIMARY, fontsize=8.5, fontweight="bold",
    )


# ---- panel: hourly performance (24 vertical bars) --------------------------------


def _draw_hourly_performance(fig, cell, hourly: Dict[str, Any]) -> None:
    ax = _new_panel_axis(fig, cell, "Hourly Performance")
    hours = list((hourly or {}).get("hours") or [])
    if not hours:
        _empty_state(ax, "No hourly data available")
        return

    hours_sorted = sorted(hours, key=lambda h: int(h.get("hour", 0) or 0))
    best_hour = (hourly or {}).get("best_hour")
    x = [int(h.get("hour", 0) or 0) for h in hours_sorted]
    values = [float(h.get("sessions", 0) or 0) for h in hours_sorted]
    colors = [STATUS_GOOD if h.get("hour") == best_hour else CATEGORICAL[0] for h in hours_sorted]

    max_value = max(values) if values else 1
    ax.set_xlim(min(x) - 0.5, max(x) + 0.5)
    ax.set_ylim(0, max_value * 1.15 if max_value else 1)
    _rounded_vbars(ax, x, values, width=0.7, colors=colors)
    ax.set_xticks(x[::3])
    ax.set_xticklabels([str(v) for v in x[::3]], color=TEXT_SECONDARY, fontsize=7.5)
    ax.set_yticks([])
    ax.grid(axis="y", color=GRID_MUTED, linewidth=0.6, zorder=0)


# ---- panel: day of week -----------------------------------------------------------


def _draw_day_of_week(fig, cell, time_patterns: Dict[str, Any]) -> None:
    day_of_week = (time_patterns or {}).get("day_of_week") or []
    ax = _new_panel_axis(fig, cell, "Day of Week")
    if not day_of_week:
        _empty_state(ax, "No day-of-week data available")
        return

    def _annotate(row, value):
        return f"{_fmt_num(value)} ({_fmt_pct(row.get('engaged_pct', 0))} eng)"

    _draw_horizontal_bars(ax, day_of_week, "day_name", "sessions", CATEGORICAL, annotate_fn=_annotate)


# ---- panel: event funnel ---------------------------------------------------------


def _draw_funnel(fig, cell, events_data: Dict[str, Any]) -> None:
    ax = _new_panel_axis(fig, cell, "Event Funnel")
    events_list = (events_data or {}).get("events") or []
    counts_by_name = {str(e.get("name")): float(e.get("count", 0) or 0) for e in events_list}
    rows = [{"step": step, "count": counts_by_name.get(step, 0.0)} for step in FUNNEL_STEPS]

    if not any(row["count"] for row in rows):
        _empty_state(ax, "No funnel event data available")
        return

    labels = [row["step"].replace("_", " ").title() for row in rows]
    values = [row["count"] for row in rows]
    y_pos = list(range(len(rows)))
    colors = list(reversed(SEQUENTIAL_BLUES))
    baseline = values[0] or 1

    max_value = max(values) if values else 1
    ax.set_xlim(0, max_value * 1.35)
    ax.set_ylim(-0.5, len(rows) - 0.5)
    _rounded_hbars(ax, y_pos, values, height=0.6, colors=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT_PRIMARY, fontsize=9)
    ax.invert_yaxis()
    ax.set_xticks([])

    for y, value in zip(y_pos, values):
        drop_pct = value / baseline * 100 if baseline else 0
        text = f"{_fmt_num(value)} ({drop_pct:.0f}%)"
        ax.text(value + max_value * 0.02, y, text, va="center", ha="left",
                 color=TEXT_PRIMARY, fontsize=8.5)


# ---- panel: full events bar list ---------------------------------------------------


def _draw_events_full(fig, cell, events_data: Dict[str, Any]) -> None:
    events_list = (events_data or {}).get("events") or []
    ax = _new_panel_axis(fig, cell, "Events")
    if not events_list:
        _empty_state(ax, "No event data available")
        return

    rows = sorted(events_list, key=lambda e: float(e.get("count", 0) or 0), reverse=True)[:EVENTS_TOP_N]

    def _annotate(row, value):
        per_user = float(row.get("per_user", 0) or 0)
        return f"{_fmt_num(value)} ({per_user:.2f}/user)"

    _draw_horizontal_bars(ax, rows, "name", "count", CATEGORICAL, annotate_fn=_annotate)


# ---- panel: technology (browsers + resolutions) -------------------------------------


def _draw_technology(fig, cell, technology: Dict[str, Any]) -> None:
    technology = technology or {}
    browsers = technology.get("browsers") or []
    resolutions = (technology.get("resolutions") or [])[:RESOLUTIONS_TOP_N]

    def _left(ax):
        _sub_label(ax, "Browsers")
        if not browsers:
            _empty_state(ax, "No browser data available")
            return

        def _annotate(row, value):
            return f"{_fmt_num(value)} ({_fmt_pct(row.get('engaged_pct', 0))})"

        _draw_horizontal_bars(ax, browsers, "name", "sessions", CATEGORICAL, annotate_fn=_annotate)

    def _right(ax):
        _sub_label(ax, "Top Resolutions")
        if not resolutions:
            _empty_state(ax, "No resolution data available")
            return

        _draw_horizontal_bars(ax, resolutions, "resolution", "sessions", CATEGORICAL)

    _draw_split_panel(fig, cell, "Technology", _left, _right)
