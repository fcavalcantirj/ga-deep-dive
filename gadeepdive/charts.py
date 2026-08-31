"""Visual dashboard renderer — a single dark-themed portrait PNG built from
stacked matplotlib panels via gridspec (Agg backend, no display, no third-party
chart deps beyond matplotlib itself).

Pure over already-collected report data (the same `data` dict `report.py`
renders): no backend calls of its own. Every panel degrades to an explicit
empty-state label when its section has no data; the GSC panel is the one
exception — it is skipped outright when GSC isn't configured/available,
mirroring the CLI's existing `--no-gsc` convention.
"""

import matplotlib

matplotlib.use("Agg")

from typing import Any, Dict, List, Optional  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import gridspec  # noqa: E402

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
FIG_HEIGHT_PX = 2400
FIG_DPI = 100
FIG_WIDTH_IN = FIG_WIDTH_PX / FIG_DPI
FIG_HEIGHT_IN = FIG_HEIGHT_PX / FIG_DPI

KPI_TILE_SPECS = [
    ("Sessions", "sessions", "num"),
    ("Users", "activeUsers", "num"),
    ("Engagement Rate", "engagementRate", "pct"),
    ("Page Views", "screenPageViews", "num"),
]

FUNNEL_STEPS = ["page_view", "example_click", "wizard_submit", "wizard_results"]

TOP_N_BARS = 8
CAPTION_LIMIT = 1024
LABEL_MAX_CHARS = 22


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


# ---- panel: header --------------------------------------------------------------


def _draw_header(fig, cell, property_name: str, period: Any, generated_at: str) -> None:
    ax = fig.add_subplot(cell)
    ax.axis("off")
    ax.text(
        0.0, 0.78, str(property_name).upper(), transform=ax.transAxes, ha="left", va="center",
        color=TEXT_PRIMARY, fontsize=26, fontweight="bold", family="sans-serif",
    )
    ax.text(
        0.0, 0.38, f"Last {period} days", transform=ax.transAxes, ha="left", va="center",
        color=TEXT_SECONDARY, fontsize=13, family="sans-serif",
    )
    ax.text(
        0.0, 0.06, f"Generated {generated_at}", transform=ax.transAxes, ha="left", va="center",
        color=TEXT_SECONDARY, fontsize=9.5, family="sans-serif",
    )


# ---- panel: KPI tiles -------------------------------------------------------------


def _draw_kpi_tiles(fig, cell, executive: Dict[str, Any]) -> None:
    inner = gridspec.GridSpecFromSubplotSpec(1, 4, subplot_spec=cell, wspace=0.14)
    current = (executive or {}).get("current") or {}
    previous = (executive or {}).get("previous") or {}

    for i, (label, key, kind) in enumerate(KPI_TILE_SPECS):
        ax = fig.add_subplot(inner[i])
        ax.set_facecolor(PANEL_BG)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        curr_value = current.get(key)
        value_str = _fmt_pct(curr_value) if kind == "pct" else _fmt_num(curr_value)
        pct_change = _wow_pct(curr_value, previous.get(key))
        if pct_change is None:
            delta_str = "NEW" if curr_value else "—"
            delta_color = TEXT_SECONDARY
        else:
            arrow = "▲" if pct_change >= 0 else "▼"
            delta_color = STATUS_GOOD if pct_change >= 0 else STATUS_CRITICAL
            delta_str = f"{arrow} {abs(pct_change):.0f}%"

        ax.text(0.5, 0.62, value_str, transform=ax.transAxes, ha="center", va="center",
                 color=TEXT_PRIMARY, fontsize=19, fontweight="bold", family="sans-serif")
        ax.text(0.5, 0.30, label.upper(), transform=ax.transAxes, ha="center", va="center",
                 color=TEXT_SECONDARY, fontsize=7.5, family="sans-serif")
        ax.text(0.5, 0.10, delta_str, transform=ax.transAxes, ha="center", va="center",
                 color=delta_color, fontsize=10, fontweight="bold", family="sans-serif")


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

    ax.barh(y_pos, values, color=colors, height=0.55, zorder=3)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT_PRIMARY, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([])
    ax.grid(axis="x", color=GRID_MUTED, linewidth=0.6, zorder=0)

    for y, (_, score) in zip(y_pos, items):
        label_text = f"{score}" if score is not None else "N/A"
        ax.text((score or 0) + 2, y, label_text, va="center", ha="left",
                 color=TEXT_PRIMARY, fontsize=9, fontweight="bold")

    overall = (health or {}).get("overall")
    overall_str = f"{overall}" if overall is not None else "N/A"
    ax.text(1.0, 1.12, f"Overall {overall_str}", transform=ax.transAxes, ha="right", va="bottom",
             color=TEXT_PRIMARY, fontsize=13, fontweight="bold", family="sans-serif")


# ---- shared: horizontal bar list panel ------------------------------------------


def _draw_horizontal_bars(ax, rows: List[Dict[str, Any]], label_key: str, value_key: str, colors: List[str],
                            annotate_fn=None) -> None:
    labels = [_truncate_label(row.get(label_key, "")) for row in rows]
    values = [float(row.get(value_key, 0) or 0) for row in rows]
    y_pos = list(range(len(labels)))
    bar_colors = [colors[i % len(colors)] for i in range(len(labels))]

    ax.barh(y_pos, values, color=bar_colors, height=0.6, zorder=3)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT_PRIMARY, fontsize=9)
    ax.invert_yaxis()
    ax.set_xticks([])

    max_value = max(values) if values else 0
    ax.set_xlim(0, max_value * 1.3 if max_value else 1)

    for y, (row, value) in zip(y_pos, zip(rows, values)):
        text = annotate_fn(row, value) if annotate_fn else _fmt_num(value)
        ax.text(value + max_value * 0.02, y, text, va="center", ha="left",
                 color=TEXT_PRIMARY, fontsize=8.5)


def _draw_horizontal_bar_panel(fig, cell, title: str, rows: List[Dict[str, Any]], label_key: str, value_key: str,
                                 colors: List[str], empty_message: str, annotate_fn=None) -> None:
    ax = _new_panel_axis(fig, cell, title)
    if not rows:
        _empty_state(ax, empty_message)
        return
    _draw_horizontal_bars(ax, rows, label_key, value_key, colors, annotate_fn=annotate_fn)


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

    ax.bar(x, values, color=colors, width=0.7, zorder=3)
    ax.set_xticks(x[::3])
    ax.set_xticklabels([str(v) for v in x[::3]], color=TEXT_SECONDARY, fontsize=7.5)
    ax.set_yticks([])
    ax.grid(axis="y", color=GRID_MUTED, linewidth=0.6, zorder=0)


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

    ax.barh(y_pos, values, color=colors, height=0.6, zorder=3)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT_PRIMARY, fontsize=9)
    ax.invert_yaxis()
    ax.set_xticks([])
    max_value = max(values) if values else 1
    ax.set_xlim(0, max_value * 1.35)

    for y, value in zip(y_pos, values):
        drop_pct = value / baseline * 100 if baseline else 0
        text = f"{_fmt_num(value)} ({drop_pct:.0f}%)"
        ax.text(value + max_value * 0.02, y, text, va="center", ha="left",
                 color=TEXT_PRIMARY, fontsize=8.5)


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

    _draw_horizontal_bars(ax, rows, "query", "impressions", CATEGORICAL, annotate_fn=_annotate)


# ---- composition ------------------------------------------------------------------


def compose_dashboard(data: Dict[str, Any], property_name: str, period: Any, output_path: str) -> str:
    """Render the full portrait dashboard PNG to `output_path` and return it."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]

    gsc = data.get("gsc")
    gsc_available = bool(gsc and gsc.get("available"))

    panel_specs = [
        ("header", 0.55),
        ("kpi", 1.05),
        ("health", 1.75),
        ("acquisition", 1.75),
        ("daily_users", 1.55),
        ("hourly", 1.4),
        ("geography", 1.75),
        ("funnel", 1.2),
    ]
    if gsc_available:
        panel_specs.append(("gsc", 1.35))

    fig = plt.figure(figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN), dpi=FIG_DPI, facecolor=SURFACE_BG)
    ratios = [height for _, height in panel_specs]
    gs = gridspec.GridSpec(
        len(panel_specs), 1, figure=fig, height_ratios=ratios, hspace=0.6,
        left=0.20, right=0.95, top=0.98, bottom=0.015,
    )
    cells = {name: gs[i] for i, (name, _) in enumerate(panel_specs)}

    _draw_header(fig, cells["header"], property_name, period, data.get("generated_at", ""))
    _draw_kpi_tiles(fig, cells["kpi"], data.get("executive") or {})
    _draw_health_scores(fig, cells["health"], data.get("health") or {})
    _draw_horizontal_bar_panel(
        fig, cells["acquisition"], "Acquisition", (data.get("acquisition") or {}).get("channels", [])[:TOP_N_BARS],
        "name", "sessions", CATEGORICAL, "No acquisition data available",
    )
    _draw_daily_users(fig, cells["daily_users"], data.get("acquisition_over_time") or {})
    _draw_hourly_performance(fig, cells["hourly"], data.get("hourly_performance") or {})
    _draw_horizontal_bar_panel(
        fig, cells["geography"], "Geography", (data.get("geography") or {}).get("countries", [])[:TOP_N_BARS],
        "name", "sessions", CATEGORICAL, "No geography data available",
    )
    _draw_funnel(fig, cells["funnel"], data.get("events") or {})
    if gsc_available:
        _draw_gsc_striking_distance(fig, cells["gsc"], gsc)

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
    for label, key, kind in KPI_TILE_SPECS:
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
