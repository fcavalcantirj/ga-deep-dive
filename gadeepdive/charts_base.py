"""Shared dashboard primitives: dark palette, geometry, formatting helpers,
rounded-bar drawing, axis scaffolding, and generic panel shapes (horizontal
bar lists, stat-tile grids, mini-tables) reused by every `charts_*` module.

Pure over already-built rows/dicts: no backend calls, no I/O. Every panel
built on top of these primitives degrades to an explicit empty-state label
when given no data — callers are responsible for the missing-data check.
"""

from typing import Any, Callable, Dict, List, Optional, Sequence

from matplotlib import gridspec
from matplotlib.patches import FancyBboxPatch

# ---- validated dark palette (do not invent colors) --------------------------

SURFACE_BG = "#1a1a19"
PANEL_BG = "#232322"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#c3c2b7"
GRID_MUTED = "#3a3a38"

STATUS_GOOD = "#0ca30c"
STATUS_WARNING = "#fab219"
STATUS_SERIOUS = "#ec835a"
STATUS_CRITICAL = "#d03b3b"

CATEGORICAL = ["#3987e5", "#008300", "#d55181", "#c98500", "#199e70", "#d95926", "#9085e9", "#e66767"]
SEQUENTIAL_BLUES = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab"]

HEALTH_BANDS = [(80, STATUS_GOOD), (60, STATUS_WARNING), (40, STATUS_SERIOUS)]

# ---- figure geometry ----------------------------------------------------------

FIG_WIDTH_PX = 1080
FIG_DPI = 100
FIG_WIDTH_IN = FIG_WIDTH_PX / FIG_DPI

# Pixel density per gridspec height-ratio unit, calibrated against the
# pre-Round-8a 8-panel baseline (2400px canvas / 12.5 ratio-units). Kept as a
# fixed constant — NOT re-derived from however many panels exist today — so
# every panel keeps its original per-row pixel budget as more panels are
# added; the canvas simply grows taller to fit them (see charts.py, which
# turns this into the actual `FIG_HEIGHT_PX` for the current panel set).
PX_PER_RATIO_UNIT = 2400 / 12.5

TOP_N_BARS = 8
CAPTION_LIMIT = 1024
LABEL_MAX_CHARS = 22
GSC_LABEL_MAX_CHARS = 34

ROUNDED_BAR_RADIUS_PX = 5
MAX_INSIGHT_CARDS = 5

ICON_SEVERITY = {"🔴": "critical", "🚨": "critical", "🟢": "good"}
SEVERITY_COLOR = {"critical": STATUS_CRITICAL, "warning": STATUS_WARNING, "good": STATUS_GOOD}


# ---- small pure formatting helpers -------------------------------------------


def _truncate_label(text: str, max_len: int = LABEL_MAX_CHARS) -> str:
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _fmt_num(value: Any) -> str:
    value = float(value or 0)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


def _fmt_pct(value: Any) -> str:
    return f"{float(value or 0) * 100:.1f}%"


def _fmt_duration(value: Any) -> str:
    return f"{float(value or 0):.0f}s"


def _fmt_decimal(value: Any) -> str:
    return f"{float(value or 0):.2f}"


def _fmt_position(value: Any) -> str:
    return f"{float(value or 0):.1f}"


def _fmt_kpi_value(value: Any, kind: str) -> str:
    if kind == "pct":
        return _fmt_pct(value)
    if kind == "duration":
        return _fmt_duration(value)
    if kind == "decimal":
        return _fmt_decimal(value)
    return _fmt_num(value)


def _wow_pct(current: Any, previous: Any) -> Optional[float]:
    current = float(current or 0)
    if not previous:
        return None
    return (current - float(previous)) / float(previous) * 100


def _health_color(score: Optional[int]) -> str:
    if score is None:
        return GRID_MUTED
    for threshold, color in HEALTH_BANDS:
        if score >= threshold:
            return color
    return STATUS_CRITICAL


def _severity_for_icon(icon: str) -> str:
    return ICON_SEVERITY.get(icon, "warning")


def _severity_color(icon: str) -> str:
    return SEVERITY_COLOR[_severity_for_icon(icon)]


def _top_insight_cards(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Reuse the exact insights the report/caption already compute, capped to
    `MAX_INSIGHT_CARDS`, each annotated with its severity color."""
    insights = (data or {}).get("insights") or []
    return [dict(insight, severity=_severity_for_icon(insight.get("icon", "")),
                 color=_severity_color(insight.get("icon", ""))) for insight in insights[:MAX_INSIGHT_CARDS]]


# ---- rounded bars ---------------------------------------------------------------


def _pixels_per_data_unit(ax) -> tuple:
    """(x, y) pixels-per-1-data-unit for `ax`, used to size a fixed-pixel
    corner radius regardless of each panel's own data scale."""
    p0 = ax.transData.transform((0, 0))
    px = ax.transData.transform((1, 0))
    py = ax.transData.transform((0, 1))
    x_px_per_unit = abs(px[0] - p0[0]) or 1.0
    y_px_per_unit = abs(py[1] - p0[1]) or 1.0
    return x_px_per_unit, y_px_per_unit


def _rounded_bar(ax, x0: float, y0: float, width: float, height: float, color: str,
                  radius_px: float = ROUNDED_BAR_RADIUS_PX, zorder: int = 3) -> FancyBboxPatch:
    """Draw a single bar/card as a `FancyBboxPatch` with a rounded-corner
    radius that reads as a fixed pixel size no matter the axis' data scale
    (via `mutation_aspect`, since a bar's x/y units are rarely 1:1 in pixels).
    """
    x_px_per_unit, y_px_per_unit = _pixels_per_data_unit(ax)
    radius_x = radius_px / x_px_per_unit
    radius_x = min(radius_x, abs(width) / 2) if width else 0.0
    aspect = x_px_per_unit / y_px_per_unit

    patch = FancyBboxPatch(
        (x0, y0), width, height,
        boxstyle=f"round,pad=0,rounding_size={radius_x}",
        mutation_aspect=aspect, mutation_scale=1,
        linewidth=0, facecolor=color, zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def _rounded_hbars(ax, y_positions: List[float], values: List[float], height: float, colors: List[str],
                    zorder: int = 3) -> None:
    for y, value, color in zip(y_positions, values, colors):
        _rounded_bar(ax, 0, y - height / 2, value, height, color, zorder=zorder)


def _rounded_vbars(ax, x_positions: List[float], values: List[float], width: float, colors: List[str],
                    zorder: int = 3) -> None:
    for x, value, color in zip(x_positions, values, colors):
        _rounded_bar(ax, x - width / 2, 0, width, value, color, zorder=zorder)


# ---- axis/panel scaffolding ---------------------------------------------------


def _style_axis(ax) -> None:
    ax.set_facecolor(PANEL_BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=8, length=0)


def _panel_title(ax, title: str) -> None:
    ax.text(
        0.0, 1.12, title.upper(), transform=ax.transAxes, ha="left", va="bottom",
        color=TEXT_SECONDARY, fontsize=10, fontweight="bold", family="sans-serif",
    )


def _sub_label(ax, text: str) -> None:
    """A smaller in-axes caption for one half of a split panel — sits just
    above the axes' own top edge, under the panel's main floating title."""
    ax.text(
        0.0, 1.0, text.upper(), transform=ax.transAxes, ha="left", va="bottom",
        color=TEXT_SECONDARY, fontsize=7.5, family="sans-serif",
    )


def _empty_state(ax, message: str) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(
        0.5, 0.5, message, transform=ax.transAxes, ha="center", va="center",
        color=TEXT_SECONDARY, fontsize=10, family="sans-serif",
    )


def _new_panel_axis(fig, cell, title: str):
    ax = fig.add_subplot(cell)
    _style_axis(ax)
    _panel_title(ax, title)
    return ax


def _draw_split_panel(fig, cell, title: str, draw_left: Callable, draw_right: Callable, wspace: float = 0.3) -> None:
    """Two side-by-side sub-panels sharing one gridspec cell and one floating
    title (anchored to the left sub-panel)."""
    inner = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=cell, wspace=wspace)
    ax_left = fig.add_subplot(inner[0])
    ax_right = fig.add_subplot(inner[1])
    _style_axis(ax_left)
    _style_axis(ax_right)
    _panel_title(ax_left, title)
    draw_left(ax_left)
    draw_right(ax_right)


# ---- shared: horizontal bar list panel ------------------------------------------


def _draw_horizontal_bars(ax, rows: List[Dict[str, Any]], label_key: str, value_key: str, colors: List[str],
                            annotate_fn=None, label_max_chars: int = LABEL_MAX_CHARS) -> None:
    labels = [_truncate_label(row.get(label_key, ""), max_len=label_max_chars) for row in rows]
    values = [float(row.get(value_key, 0) or 0) for row in rows]
    y_pos = list(range(len(labels)))
    bar_colors = [colors[i % len(colors)] for i in range(len(labels))]

    max_value = max(values) if values else 0
    ax.set_xlim(0, max_value * 1.3 if max_value else 1)
    ax.set_ylim(-0.5, len(labels) - 0.5 if labels else 0.5)
    _rounded_hbars(ax, y_pos, values, height=0.6, colors=bar_colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT_PRIMARY, fontsize=9)
    ax.invert_yaxis()
    ax.set_xticks([])

    for y, (row, value) in zip(y_pos, zip(rows, values)):
        text = annotate_fn(row, value) if annotate_fn else _fmt_num(value)
        ax.text(value + max_value * 0.02, y, text, va="center", ha="left",
                 color=TEXT_PRIMARY, fontsize=8.5)


def _draw_horizontal_bar_panel(fig, cell, title: str, rows: List[Dict[str, Any]], label_key: str, value_key: str,
                                 colors: List[str], empty_message: str, annotate_fn=None,
                                 label_max_chars: int = LABEL_MAX_CHARS) -> None:
    ax = _new_panel_axis(fig, cell, title)
    if not rows:
        _empty_state(ax, empty_message)
        return
    _draw_horizontal_bars(ax, rows, label_key, value_key, colors, annotate_fn=annotate_fn, label_max_chars=label_max_chars)


# ---- shared: stat-tile grid (KPI tiles, chip rows) --------------------------------


def _draw_tile(ax, value: str, label: str, delta: Optional[str] = None,
               value_color: str = TEXT_PRIMARY, delta_color: str = TEXT_SECONDARY,
               value_fontsize: float = 17) -> None:
    ax.set_facecolor(PANEL_BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    value_y = 0.62 if delta is not None else 0.55
    ax.text(0.5, value_y, value, transform=ax.transAxes, ha="center", va="center",
             color=value_color, fontsize=value_fontsize, fontweight="bold", family="sans-serif")
    ax.text(0.5, 0.28, label.upper(), transform=ax.transAxes, ha="center", va="center",
             color=TEXT_SECONDARY, fontsize=7.2, family="sans-serif")
    if delta is not None:
        ax.text(0.5, 0.08, delta, transform=ax.transAxes, ha="center", va="center",
                 color=delta_color, fontsize=9.5, fontweight="bold", family="sans-serif")


def _draw_tiles_panel(fig, cell, title: str, tiles: List[Dict[str, Any]], ncols: int, empty_message: str) -> None:
    """A titled grid of equal-width stat tiles (KPI tiles or plain chips).
    Each tile dict: {"value", "label", "delta"?, "value_color"?, "delta_color"?}.
    """
    if not tiles:
        ax = _new_panel_axis(fig, cell, title)
        _empty_state(ax, empty_message)
        return

    nrows = -(-len(tiles) // ncols)
    inner = gridspec.GridSpecFromSubplotSpec(nrows, ncols, subplot_spec=cell, wspace=0.14, hspace=0.55)
    first_ax = None
    for i, tile in enumerate(tiles):
        r, c = divmod(i, ncols)
        ax = fig.add_subplot(inner[r, c])
        if first_ax is None:
            first_ax = ax
        _draw_tile(
            ax, tile["value"], tile["label"], delta=tile.get("delta"),
            value_color=tile.get("value_color", TEXT_PRIMARY), delta_color=tile.get("delta_color", TEXT_SECONDARY),
            value_fontsize=tile.get("value_fontsize", 17),
        )
    _panel_title(first_ax, title)


# ---- shared: mini-table (categorical text on the panel background) ---------------


def _draw_mini_table(ax, headers: Sequence[str], rows: List[Sequence[str]], col_x: Sequence[float],
                      col_align: Sequence[str], empty_message: str) -> None:
    """A clean styled key/value table rendered directly on the panel
    background — used for categorical report data (attribution, top
    queries, trending pages, ...) instead of dumping raw ANSI text."""
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    if not rows:
        _empty_state(ax, empty_message)
        return

    n = len(rows) + 1
    row_h = 1.0 / n
    header_y = 1.0 - row_h * 0.5
    for x, text, align in zip(col_x, headers, col_align):
        ax.text(x, header_y, str(text).upper(), ha=align, va="center",
                 color=TEXT_SECONDARY, fontsize=7.5, fontweight="bold", family="sans-serif")

    sep_y = 1.0 - row_h
    ax.plot([0, 1], [sep_y, sep_y], color=GRID_MUTED, linewidth=0.8, transform=ax.transAxes, zorder=1)

    for i, row in enumerate(rows):
        y = 1.0 - row_h * (i + 1) - row_h * 0.5
        for x, text, align in zip(col_x, row, col_align):
            ax.text(x, y, str(text), ha=align, va="center",
                     color=TEXT_PRIMARY, fontsize=8.5, family="sans-serif")


def _draw_mini_table_panel(fig, cell, title: str, headers: Sequence[str], rows: List[Sequence[str]],
                            col_x: Sequence[float], col_align: Sequence[str], empty_message: str) -> None:
    ax = _new_panel_axis(fig, cell, title)
    _draw_mini_table(ax, headers, rows, col_x, col_align, empty_message)
