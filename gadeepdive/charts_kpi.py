"""Header area panels: property banner, LIVE NOW badge, the full executive-
summary KPI tile grid (WoW arrows, correct polarity for reversed metrics
like Bounce Rate), and the DAU/WAU/MAU user-activity stat chips.
"""

from typing import Any, Dict, List, Tuple

from .charts_base import (
    STATUS_CRITICAL,
    STATUS_GOOD,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    _draw_tiles_panel,
    _fmt_kpi_value,
    _fmt_num,
    _fmt_pct,
    _wow_pct,
)

# label, executive-summary key, reverse-polarity (down=good), value kind
KPI_TILE_SPECS: List[Tuple[str, str, bool, str]] = [
    ("Sessions", "sessions", False, "num"),
    ("Users", "activeUsers", False, "num"),
    ("New Users", "newUsers", False, "num"),
    ("Engaged Sessions", "engagedSessions", False, "num"),
    ("Engagement Rate", "engagementRate", False, "pct"),
    ("Bounce Rate", "bounceRate", True, "pct"),
    ("Avg Duration", "averageSessionDuration", False, "duration"),
    ("Pages/Session", "screenPageViewsPerSession", False, "decimal"),
    ("Page Views", "screenPageViews", False, "num"),
]
KPI_GRID_COLS = 3

ACTIVITY_CHIP_SPECS: List[Tuple[str, str, str]] = [
    ("DAU", "active1DayUsers", "int"),
    ("WAU", "active7DayUsers", "int"),
    ("MAU", "active28DayUsers", "int"),
    ("DAU/WAU", "dauPerWau", "pct"),
    ("DAU/MAU", "dauPerMau", "pct"),
]


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


# ---- panel: live now badge -------------------------------------------------------


def _draw_live_now(fig, cell, realtime: Dict[str, Any]) -> None:
    ax = fig.add_subplot(cell)
    ax.axis("off")
    ax.set_facecolor("none")
    active = (realtime or {}).get("active_users")
    if active is None:
        ax.text(0.0, 0.5, "No realtime data available", transform=ax.transAxes, ha="left", va="center",
                 color=TEXT_SECONDARY, fontsize=10, family="sans-serif")
        return

    ax.scatter([0.012], [0.5], s=70, color=STATUS_GOOD, zorder=4, transform=ax.transAxes)
    label = f"LIVE NOW — {int(active)} active user{'s' if active != 1 else ''}"
    ax.text(0.035, 0.5, label, transform=ax.transAxes, ha="left", va="center",
             color=TEXT_PRIMARY, fontsize=11, fontweight="bold", family="sans-serif")


# ---- panel: KPI tiles -------------------------------------------------------------


def _draw_kpi_tiles(fig, cell, executive: Dict[str, Any]) -> None:
    current = (executive or {}).get("current") or {}
    previous = (executive or {}).get("previous") or {}

    tiles = []
    for label, key, reverse, kind in KPI_TILE_SPECS:
        curr_value = current.get(key)
        value_str = _fmt_kpi_value(curr_value, kind)
        pct_change = _wow_pct(curr_value, previous.get(key))
        if pct_change is None:
            delta_str = "NEW" if curr_value else "—"
            delta_color = TEXT_SECONDARY
        else:
            arrow = "▲" if pct_change >= 0 else "▼"
            is_good = (pct_change <= 0) if reverse else (pct_change >= 0)
            delta_color = STATUS_GOOD if is_good else STATUS_CRITICAL
            delta_str = f"{arrow} {abs(pct_change):.0f}%"
        tiles.append({"value": value_str, "label": label, "delta": delta_str, "delta_color": delta_color})

    _draw_tiles_panel(fig, cell, "Executive Summary", tiles, KPI_GRID_COLS, "No executive summary data available")


# ---- panel: user activity (DAU/WAU/MAU + stickiness) ------------------------------


def _draw_user_activity(fig, cell, activity: Dict[str, Any]) -> None:
    activity = activity or {}
    if not activity:
        _draw_tiles_panel(fig, cell, "User Activity", [], len(ACTIVITY_CHIP_SPECS), "No user activity data available")
        return

    tiles = []
    for label, key, kind in ACTIVITY_CHIP_SPECS:
        value = activity.get(key)
        value_str = _fmt_pct(value) if kind == "pct" else _fmt_num(value)
        tiles.append({"value": value_str, "label": label, "value_fontsize": 14})

    _draw_tiles_panel(fig, cell, "User Activity", tiles, len(ACTIVITY_CHIP_SPECS), "No user activity data available")
