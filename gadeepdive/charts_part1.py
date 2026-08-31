"""PART 1 panels: health scores, acquisition detail (top referrer +
first-touch attribution), geography languages, content, and user segments.
The acquisition/geography *bar* panels themselves are drawn with the generic
`_draw_horizontal_bar_panel` directly from the compose module — this module
covers the panels that don't fit that generic shape.
"""

from typing import Any, Dict

from .charts_base import (
    CATEGORICAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    _draw_horizontal_bars,
    _draw_mini_table,
    _empty_state,
    _fmt_num,
    _fmt_pct,
    _health_color,
    _new_panel_axis,
    _rounded_hbars,
    _draw_split_panel,
    _sub_label,
)

LANGUAGES_TOP_N = 5
FIRST_TOUCH_TOP_N = 8
CONTENT_LIST_TOP_N = 5

# ---- panel: health scores ------------------------------------------------------


def _draw_health_scores(fig, cell, health: Dict[str, Any]) -> None:
    ax = _new_panel_axis(fig, cell, "Health Scores")
    scores = (health or {}).get("scores") or {}
    if not scores:
        _empty_state(ax, "No health data available")
        return

    items = sorted(scores.items(), key=lambda kv: kv[1] if kv[1] is not None else -1, reverse=True)
    labels = [label for label, _ in items]
    values = [score if score is not None else 0 for _, score in items]
    colors = [_health_color(score) for _, score in items]
    y_pos = list(range(len(labels)))

    ax.set_xlim(0, 100)
    ax.set_ylim(-0.5, len(labels) - 0.5)
    _rounded_hbars(ax, y_pos, values, height=0.55, colors=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT_PRIMARY, fontsize=9)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.grid(axis="x", color="#3a3a38", linewidth=0.6, zorder=0)

    for y, (_, score) in zip(y_pos, items):
        label_text = f"{score}" if score is not None else "N/A"
        ax.text((score or 0) + 2, y, label_text, va="center", ha="left",
                 color=TEXT_PRIMARY, fontsize=9, fontweight="bold")

    overall = (health or {}).get("overall")
    overall_str = f"{overall}" if overall is not None else "N/A"
    ax.text(1.0, 1.12, f"Overall {overall_str}", transform=ax.transAxes, ha="right", va="bottom",
             color=TEXT_PRIMARY, fontsize=13, fontweight="bold", family="sans-serif")


# ---- panel: acquisition detail (top referrer + first-touch attribution) ----------


def _draw_acquisition_detail(fig, cell, acquisition: Dict[str, Any]) -> None:
    acquisition = acquisition or {}
    ax = _new_panel_axis(fig, cell, "Top Referrer & Attribution")
    top_referrer = acquisition.get("top_referrer")
    first_touch = acquisition.get("first_touch") or []

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    if not top_referrer and not first_touch:
        _empty_state(ax, "No attribution data available")
        return

    referrer_text = (
        f"Top Referrer: {top_referrer['source_medium']} — {_fmt_num(top_referrer['sessions'])} sessions"
        if top_referrer else "Top Referrer: no referral traffic"
    )
    ax.text(0.0, 0.96, referrer_text, ha="left", va="top", color=TEXT_PRIMARY, fontsize=9.5, fontweight="bold")

    rows = [
        [ft["source"], ft["medium"], _fmt_num(ft["sessions"]), _fmt_pct(ft["share"])]
        for ft in first_touch[:FIRST_TOUCH_TOP_N]
    ]
    # Reserve the top ~18% of the panel for the referrer line above.
    sub_ax = ax.inset_axes([0, 0, 1, 0.82])
    sub_ax.set_xticks([])
    sub_ax.set_yticks([])
    for spine in sub_ax.spines.values():
        spine.set_visible(False)
    sub_ax.set_facecolor("none")
    _draw_mini_table(
        sub_ax, ["Source", "Medium", "Sessions", "Share"], rows,
        col_x=[0.0, 0.4, 0.75, 1.0], col_align=["left", "left", "right", "right"],
        empty_message="no first-touch data",
    )


# ---- panel: geography languages --------------------------------------------------


def _draw_geography_languages(fig, cell, geography: Dict[str, Any]) -> None:
    languages = ((geography or {}).get("languages") or [])[:LANGUAGES_TOP_N]
    ax = _new_panel_axis(fig, cell, "Languages")
    if not languages:
        _empty_state(ax, "No language data available")
        return

    def _annotate(row, value):
        return f"{_fmt_num(value)} · {_fmt_pct(row.get('share', 0))}"

    _draw_horizontal_bars(ax, languages, "name", "sessions", CATEGORICAL, annotate_fn=_annotate)


# ---- panel: content bars ----------------------------------------------------------


def _draw_content_bars(fig, cell, content: Dict[str, Any]) -> None:
    sections = (content or {}).get("sections") or []
    ax = _new_panel_axis(fig, cell, "Content")
    if not sections:
        _empty_state(ax, "No content data available")
        return

    def _annotate(row, value):
        return f"{_fmt_num(value)} ({_fmt_pct(row.get('engagement_pct', 0))})"

    _draw_horizontal_bars(ax, sections, "section", "views", CATEGORICAL, annotate_fn=_annotate)


# ---- panel: content trending up / problem pages -----------------------------------


def _draw_content_lists(fig, cell, content: Dict[str, Any]) -> None:
    content = content or {}
    trending = (content.get("trending_up") or [])[:CONTENT_LIST_TOP_N]
    problems = (content.get("problem_pages") or [])[:CONTENT_LIST_TOP_N]

    def _left(ax):
        _sub_label(ax, "Trending Up")
        rows = [[t["path"], f"+{t['pct_change'] * 100:.0f}%"] for t in trending]
        _draw_mini_table(ax, ["Page", "+% WoW"], rows, col_x=[0.0, 1.0], col_align=["left", "right"],
                          empty_message="no WoW gainers")

    def _right(ax):
        _sub_label(ax, "Problem Pages")
        rows = [[p["path"], _fmt_pct(p["bounce_pct"])] for p in problems]
        _draw_mini_table(ax, ["Page", "Bounce%"], rows, col_x=[0.0, 1.0], col_align=["left", "right"],
                          empty_message="none")

    _draw_split_panel(fig, cell, "Content Trends", _left, _right)


# ---- panel: user segments -----------------------------------------------------------


def _draw_user_segments(fig, cell, segments: Dict[str, Any]) -> None:
    segments = segments or {}
    new_vs_returning = segments.get("new_vs_returning") or []
    by_device = segments.get("by_device") or []

    def _left(ax):
        _sub_label(ax, "New vs Returning")
        if not new_vs_returning:
            _empty_state(ax, "No segment data available")
            return

        def _annotate(row, value):
            return f"{_fmt_num(value)} ({_fmt_pct(row.get('engagement_pct', 0))})"

        _draw_horizontal_bars(ax, new_vs_returning, "segment", "sessions", CATEGORICAL, annotate_fn=_annotate)

    def _right(ax):
        _sub_label(ax, "By Device")
        if not by_device:
            _empty_state(ax, "No device data available")
            return

        def _annotate(row, value):
            return _fmt_pct(value)

        _draw_horizontal_bars(ax, by_device, "device", "share", CATEGORICAL, annotate_fn=_annotate)

    _draw_split_panel(fig, cell, "User Segments", _left, _right)
