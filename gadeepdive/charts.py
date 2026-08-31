"""Visual dashboard renderer — a single dark-themed portrait PNG built from
stacked matplotlib panels via gridspec (Agg backend, no display, no third-party
chart deps beyond matplotlib itself).

Pure over already-collected report data (the same `data` dict `report.py`
renders): no backend calls of its own. Every panel degrades to an explicit
empty-state label when its section has no data; the GSC panels are the one
exception — they are skipped outright when GSC isn't configured/available,
mirroring the CLI's existing `--no-gsc` convention.

This module is the *composition* layer: it lays out every panel in report
order and owns the two functions the rest of the app calls
(`compose_dashboard`, `compose_caption`). The panels themselves live in the
`charts_base`/`charts_kpi`/`charts_part1`/`charts_activity`/`charts_part2`/
`charts_gsc` sibling modules, split out so no single file grows past ~900
lines. `_draw_gsc_striking_distance`, `_draw_pacing_panel` and
`_draw_insights_panel` stay defined here (rather than in a sibling module)
because existing tests monkeypatch them as `charts.<name>` and rely on that
patch being visible to `compose_dashboard`'s own module-global lookup.
"""

import matplotlib

matplotlib.use("Agg")

from typing import Any, Dict  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import gridspec  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from . import northstar  # noqa: E402
from .charts_activity import (  # noqa: E402
    _draw_day_of_week,
    _draw_daily_users,
    _draw_events_full,
    _draw_funnel,
    _draw_hourly_performance,
    _draw_technology,
)
from .charts_base import (  # noqa: E402
    CATEGORICAL,
    FIG_DPI,
    FIG_WIDTH_IN,
    FIG_WIDTH_PX,
    GSC_LABEL_MAX_CHARS,
    LABEL_MAX_CHARS,
    PX_PER_RATIO_UNIT,
    STATUS_CRITICAL,
    STATUS_GOOD,
    STATUS_WARNING,
    SURFACE_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    CAPTION_LIMIT,
    _draw_horizontal_bar_panel,
    _draw_horizontal_bars,
    _empty_state,
    _fmt_num,
    _fmt_pct,
    _new_panel_axis,
    _rounded_bar,
    _severity_color,
    _severity_for_icon,
    _top_insight_cards,
    _truncate_label,
    _wow_pct,
)
from .charts_gsc import _draw_gsc_top_queries, _draw_gsc_totals  # noqa: E402
from .charts_kpi import KPI_TILE_SPECS, _draw_header, _draw_kpi_tiles, _draw_live_now, _draw_user_activity  # noqa: E402
from .charts_part1 import (  # noqa: E402
    _draw_acquisition_detail,
    _draw_content_bars,
    _draw_content_lists,
    _draw_geography_languages,
    _draw_health_scores,
    _draw_user_segments,
)
from .charts_part2 import _draw_audiences, _draw_entry_points, _draw_mobile_devices, _draw_scroll_depth  # noqa: E402

TOP_N_BARS = 8
CAPTION_KPI_LABELS = ["Sessions", "Users", "Engagement Rate", "Page Views"]


# ---- panel: GSC striking distance -------------------------------------------------


def _draw_gsc_striking_distance(fig, cell, gsc: Dict[str, Any]) -> None:
    ax = _new_panel_axis(fig, cell, "GSC Striking Distance")
    striking = (gsc or {}).get("striking_distance") or []
    if not striking:
        _empty_state(ax, "No striking-distance queries")
        return

    rows = sorted(striking, key=lambda q: float(q.get("impressions", 0) or 0), reverse=True)[:TOP_N_BARS]

    def _annotate(row: Dict[str, Any], value: float) -> str:
        position = float(row.get("position", 0) or 0)
        return f"{_fmt_num(value)} imp · pos {position:.1f}"

    _draw_horizontal_bars(ax, rows, "query", "impressions", CATEGORICAL, annotate_fn=_annotate,
                           label_max_chars=GSC_LABEL_MAX_CHARS)


# ---- panel: actionable insights (callout cards) ----------------------------------

CARD_GAP_FRAC = 0.14


def _draw_insights_panel(fig, cell, data: Dict[str, Any]) -> None:
    ax = _new_panel_axis(fig, cell, "Actionable Insights")
    cards = _top_insight_cards(data)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    if not cards:
        _empty_state(ax, "No actionable insights")
        return

    n = len(cards)
    slot_height = 1.0 / n
    gap = slot_height * CARD_GAP_FRAC
    card_height = slot_height - gap

    for i, card in enumerate(cards):
        y0 = 1.0 - (i + 1) * slot_height + gap / 2
        _rounded_bar(ax, 0.01, y0, 0.98, card_height, "#232322", radius_px=8, zorder=2)
        stripe = Rectangle((0.01, y0), 0.012, card_height, linewidth=0, facecolor=card["color"], zorder=3)
        ax.add_patch(stripe)

        # A plain dot, not the insight's own emoji: matplotlib's default sans
        # font has no color-emoji glyphs, so printing 🔴/🚨/🟢 as text renders
        # as missing-glyph tofu boxes in the rasterized PNG.
        icon_y = y0 + card_height * 0.62
        ax.scatter([0.045], [icon_y], s=50, color=card["color"], zorder=4)
        message = card.get("message", "")
        ax.text(0.075, icon_y, message, ha="left", va="center",
                 color=TEXT_PRIMARY, fontsize=9.5, fontweight="bold")
        action = card.get("action")
        if action:
            ax.text(0.075, y0 + card_height * 0.25, f"→ {action}", ha="left", va="center",
                     color=TEXT_SECONDARY, fontsize=8.5)


# ---- panel: north-star pacing (optional, registry-driven goal) -------------------


def _draw_pacing_panel(fig, cell, pacing: Dict[str, Any]) -> None:
    ax = _new_panel_axis(fig, cell, "North-Star Pacing")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1)

    percent = max(0.0, min(pacing["percent"], 100.0))
    _rounded_bar(ax, 0, 0.55, 100, 0.28, "#3a3a38", radius_px=6, zorder=2)
    if percent > 0:
        _rounded_bar(ax, 0, 0.55, percent, 0.28, "#3987e5", radius_px=6, zorder=3)

    ax.text(0.0, 1.0, pacing["label"], transform=ax.transAxes, ha="left", va="bottom",
             color=TEXT_PRIMARY, fontsize=11, fontweight="bold")
    ax.text(1.0, 1.0, f"{pacing['percent']:.1f}% of target", transform=ax.transAxes, ha="right", va="bottom",
             color=TEXT_SECONDARY, fontsize=9.5)

    ax.text(0.0, 0.30, f"{_fmt_num(pacing['current_total'])} of {_fmt_num(pacing['target'])}", transform=ax.transAxes,
             ha="left", va="center", color=TEXT_PRIMARY, fontsize=10)
    ax.text(0.0, 0.08, f"{pacing['days_left']} days left", transform=ax.transAxes, ha="left", va="center",
             color=TEXT_SECONDARY, fontsize=9)

    ahead = pacing["ahead"]
    status_color = STATUS_GOOD if ahead else STATUS_CRITICAL
    status_text = "AHEAD OF PACE" if ahead else "BEHIND PACE"
    ax.text(
        1.0, 0.08,
        f"{status_text} · need {_fmt_num(pacing['required_rate'])}/day vs {_fmt_num(pacing['current_rate'])}/day",
        transform=ax.transAxes, ha="right", va="center", color=status_color, fontsize=9, fontweight="bold",
    )


# ---- composition ------------------------------------------------------------------

# Always-rendered panels, in the same order as the full-text report — every
# section degrades to an empty-state label internally when its data is
# missing, so nothing here is conditional on data presence (only on whether
# the *section itself* is optional, like GSC/pacing below).
BASE_PANEL_SPECS = [
    ("header", 0.55),
    ("live_now", 0.35),
    # 3 rows of tiles (9 executive-summary metrics at 3/row) — 3x the
    # original single-row ratio (1.05) so each row keeps the same height.
    ("kpi", 3.3),
    ("user_activity", 0.55),
    ("health", 1.75),
    ("acquisition", 1.75),
    ("acquisition_detail", 1.5),
    ("daily_users", 1.55),
    ("hourly", 1.4),
    ("day_of_week", 1.3),
    ("geography", 1.75),
    ("geography_languages", 1.1),
    ("content_bars", 1.4),
    ("content_lists", 1.4),
    ("user_segments", 1.3),
    ("funnel", 1.2),
    ("events_full", 1.7),
    ("technology", 1.5),
    ("scroll_depth", 1.5),
    ("entry_points", 1.4),
    ("audiences", 1.3),
    ("mobile_devices", 1.4),
]
INSIGHTS_PANEL_RATIO = 1.5
GSC_TOTALS_PANEL_RATIO = 0.55
GSC_TOP_QUERIES_PANEL_RATIO = 1.6
GSC_PANEL_RATIO = 1.35
PACING_PANEL_RATIO = 1.1

# `PX_PER_RATIO_UNIT` is a fixed density (see charts_base), so every panel
# keeps the same per-row pixel budget the baseline design was tuned for; the
# baseline canvas height below is *derived* from however many panels exist
# today, rather than the panel list being squeezed to fit a fixed height. GSC
# and the optional pacing panel grow the canvas further still, beyond this
# baseline.
_BASELINE_RATIO_SUM = sum(ratio for _, ratio in BASE_PANEL_SPECS) + INSIGHTS_PANEL_RATIO
FIG_HEIGHT_PX = round(PX_PER_RATIO_UNIT * _BASELINE_RATIO_SUM)


def compose_dashboard(data: Dict[str, Any], property_name: str, period: Any, output_path: str) -> str:
    """Render the full portrait dashboard PNG to `output_path` and return it."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]

    gsc = data.get("gsc")
    gsc_available = bool(gsc and gsc.get("available"))
    pacing = northstar.compute_pacing(data, data.get("goal"))

    panel_specs = list(BASE_PANEL_SPECS)
    if gsc_available:
        panel_specs.append(("gsc_totals", GSC_TOTALS_PANEL_RATIO))
        panel_specs.append(("gsc_top_queries", GSC_TOP_QUERIES_PANEL_RATIO))
        panel_specs.append(("gsc", GSC_PANEL_RATIO))
    panel_specs.append(("insights", INSIGHTS_PANEL_RATIO))
    if pacing:
        panel_specs.append(("pacing", PACING_PANEL_RATIO))

    total_ratio = sum(ratio for _, ratio in panel_specs)
    fig_height_in = (PX_PER_RATIO_UNIT * total_ratio) / FIG_DPI

    fig = plt.figure(figsize=(FIG_WIDTH_IN, fig_height_in), dpi=FIG_DPI, facecolor=SURFACE_BG)
    ratios = [height for _, height in panel_specs]
    gs = gridspec.GridSpec(
        len(panel_specs), 1, figure=fig, height_ratios=ratios, hspace=0.75,
        left=0.24, right=0.95, top=0.99, bottom=0.008,
    )
    cells = {name: gs[i] for i, (name, _) in enumerate(panel_specs)}

    _draw_header(fig, cells["header"], property_name, period, data.get("generated_at", ""))
    _draw_live_now(fig, cells["live_now"], data.get("realtime") or {})
    _draw_kpi_tiles(fig, cells["kpi"], data.get("executive") or {})
    _draw_user_activity(fig, cells["user_activity"], data.get("activity") or {})
    _draw_health_scores(fig, cells["health"], data.get("health") or {})
    _draw_horizontal_bar_panel(
        fig, cells["acquisition"], "Acquisition", (data.get("acquisition") or {}).get("channels", [])[:TOP_N_BARS],
        "name", "sessions", CATEGORICAL, "No acquisition data available",
    )
    _draw_acquisition_detail(fig, cells["acquisition_detail"], data.get("acquisition") or {})
    _draw_daily_users(fig, cells["daily_users"], data.get("acquisition_over_time") or {})
    _draw_hourly_performance(fig, cells["hourly"], data.get("hourly_performance") or {})
    _draw_day_of_week(fig, cells["day_of_week"], data.get("time_patterns") or {})
    _draw_horizontal_bar_panel(
        fig, cells["geography"], "Geography", (data.get("geography") or {}).get("countries", [])[:TOP_N_BARS],
        "name", "sessions", CATEGORICAL, "No geography data available",
    )
    _draw_geography_languages(fig, cells["geography_languages"], data.get("geography") or {})
    _draw_content_bars(fig, cells["content_bars"], data.get("content") or {})
    _draw_content_lists(fig, cells["content_lists"], data.get("content") or {})
    _draw_user_segments(fig, cells["user_segments"], data.get("segments") or {})
    _draw_funnel(fig, cells["funnel"], data.get("events") or {})
    _draw_events_full(fig, cells["events_full"], data.get("events") or {})
    _draw_technology(fig, cells["technology"], data.get("technology") or {})
    _draw_scroll_depth(fig, cells["scroll_depth"], data.get("scroll_depth") or {})
    _draw_entry_points(fig, cells["entry_points"], data.get("user_flow") or {})
    _draw_audiences(fig, cells["audiences"], data.get("audiences") or {})
    _draw_mobile_devices(fig, cells["mobile_devices"], data.get("mobile_devices") or {})
    if gsc_available:
        _draw_gsc_totals(fig, cells["gsc_totals"], gsc)
        _draw_gsc_top_queries(fig, cells["gsc_top_queries"], gsc)
        _draw_gsc_striking_distance(fig, cells["gsc"], gsc)
    _draw_insights_panel(fig, cells["insights"], data)
    if pacing:
        _draw_pacing_panel(fig, cells["pacing"], pacing)

    fig.savefig(output_path, dpi=FIG_DPI, facecolor=SURFACE_BG)
    plt.close(fig)
    return output_path


def compose_caption(data: Dict[str, Any], property_name: str, period: Any) -> str:
    """Build the short plain-text Telegram caption: property + period + the
    4 headline KPIs (WoW arrows) + top 3 actionable insights + top
    striking-distance query. Always kept under `CAPTION_LIMIT` chars."""
    lines = [f"{str(property_name).upper()} — Last {period} days"]

    executive = data.get("executive") or {}
    current = executive.get("current") or {}
    previous = executive.get("previous") or {}
    kpi_bits = []
    caption_specs = [(label, key, kind) for label, key, _reverse, kind in KPI_TILE_SPECS if label in CAPTION_KPI_LABELS]
    for label, key, kind in caption_specs:
        curr_value = current.get(key)
        value_str = _fmt_pct(curr_value) if kind == "pct" else _fmt_num(curr_value)
        pct_change = _wow_pct(curr_value, previous.get(key))
        if pct_change is None:
            change_str = "NEW" if curr_value else "—"
        else:
            arrow = "▲" if pct_change >= 0 else "▼"
            change_str = f"{arrow}{abs(pct_change):.0f}%"
        kpi_bits.append(f"{label} {value_str} {change_str}")
    lines.append(" | ".join(kpi_bits))

    for insight in (data.get("insights") or [])[:3]:
        message = insight.get("message")
        if message:
            lines.append(f"• {message}")

    gsc = data.get("gsc") or {}
    striking = gsc.get("striking_distance") or []
    if striking:
        top = max(striking, key=lambda q: float(q.get("impressions", 0) or 0))
        position = float(top.get("position", 0) or 0)
        impressions = _fmt_num(top.get("impressions", 0))
        lines.append(f"Top striking-distance query: \"{top.get('query')}\" (pos {position:.1f}, {impressions} impr)")

    caption = "\n".join(lines)
    if len(caption) > CAPTION_LIMIT:
        caption = caption[: CAPTION_LIMIT - 3] + "..."
    return caption
