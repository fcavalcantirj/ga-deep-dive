"""Pure rendering of PART 1 §1-4 (banner, LIVE NOW, EXECUTIVE SUMMARY, HEALTH
DASHBOARD). Data in, string (or dict, for json mode) out — no I/O, no clock.

Three render modes:
- "full": ANSI report with box-art banner (default).
- "telegram": width-safe condensed variant, no box-art.
- "json": the same data as a plain dict (no art at all).
"""

from typing import Any, Dict, List, Optional, Tuple

BOX_WIDTH = 78

EXEC_METRIC_SPECS: List[Tuple[str, str, bool, str]] = [
    ("Sessions", "sessions", False, "num"),
    ("Users", "activeUsers", False, "num"),
    ("New Users", "newUsers", False, "num"),
    ("Engaged Sessions", "engagedSessions", False, "num"),
    ("Engagement Rate", "engagementRate", False, "pct"),
    ("Bounce Rate", "bounceRate", True, "pct"),
    ("Avg Duration (s)", "averageSessionDuration", False, "duration"),
    ("Pages/Session", "screenPageViewsPerSession", False, "decimal"),
    ("Page Views", "screenPageViews", False, "num"),
]

HEALTH_LABELS = ["Growth", "Content", "Engagement", "Mobile", "Geo Diversity", "Retention", "Traffic Diversity"]


# ---- formatting helpers ------------------------------------------------------


def fmt_num(n: float) -> str:
    n = float(n or 0)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(int(n))


def fmt_pct(value: float, decimals: int = 1) -> str:
    return f"{float(value or 0) * 100:.{decimals}f}%"


def fmt_value(value: float, kind: str) -> str:
    if kind == "pct":
        return fmt_pct(value)
    if kind == "duration":
        return f"{float(value or 0):.0f}s"
    if kind == "decimal":
        return f"{float(value or 0):.2f}"
    return fmt_num(value)


def delta_arrow(current: float, previous: Optional[float], reverse: bool = False) -> str:
    """WoW change indicator. `reverse=True` means down is good (e.g. bounce rate)."""
    current = float(current or 0)
    if not previous:
        return "NEW" if current > 0 else "—"
    change = (current - previous) / previous * 100
    if reverse:
        change = -change
    if change > 10:
        return f"🟢 +{change:.0f}%"
    if change > 0:
        return f"↑{change:.0f}%"
    if change < -10:
        return f"🔴 {change:.0f}%"
    if change < 0:
        return f"↓{abs(change):.0f}%"
    return "→"


def bar(value: float, max_value: float = 100, width: int = 20) -> str:
    if max_value == 0:
        return "░" * width
    filled = max(0, min(width, int(value / max_value * width)))
    return "█" * filled + "░" * (width - filled)


def _status_icon(score: int) -> str:
    if score >= 80:
        return "✅"
    if score >= 60:
        return "⚠️"
    return "🔴"


def _sorted_scores(scores: Dict[str, Optional[int]]) -> List[Tuple[str, Optional[int]]]:
    return sorted(scores.items(), key=lambda item: item[1] if item[1] is not None else -1, reverse=True)


# ---- section builders (mode-agnostic content, mode-specific formatting) -----


def _banner_lines(data: Dict[str, Any]) -> List[str]:
    return [
        "🏴‍☠️  GA4 DEEP DIVE v3 — THE OWNER'S WAR ROOM",
        "",
        f"Property: {data['property'].upper()}     Period: Last {data['days']} days",
        f"Generated: {data['generated_at']}",
    ]


def _live_now_line(data: Dict[str, Any]) -> str:
    n = data["realtime"]["active_users"]
    return f"🟢 LIVE NOW: {n} active user{'s' if n != 1 else ''}"


def _exec_summary_rows(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    current = data["executive"]["current"]
    previous = data["executive"]["previous"]
    rows = []
    for label, key, reverse, kind in EXEC_METRIC_SPECS:
        curr_value = current.get(key, 0)
        prev_value = previous.get(key)
        rows.append(
            {
                "label": label,
                "current_str": fmt_value(curr_value, kind),
                "previous_str": fmt_value(prev_value, kind) if prev_value else "—",
                "change": delta_arrow(curr_value, prev_value, reverse),
            }
        )
    return rows


def _activity_lines(data: Dict[str, Any]) -> List[str]:
    activity = data["activity"]
    dau = int(activity.get("active1DayUsers", 0) or 0)
    wau = int(activity.get("active7DayUsers", 0) or 0)
    mau = int(activity.get("active28DayUsers", 0) or 0)
    lines = [f"DAU: {dau:,}  |  WAU: {wau:,}  |  MAU: {mau:,}"]
    dau_wau = activity.get("dauPerWau")
    dau_mau = activity.get("dauPerMau")
    if dau_wau is not None and dau_mau is not None:
        lines.append(f"Stickiness: DAU/WAU={fmt_pct(dau_wau)}  DAU/MAU={fmt_pct(dau_mau)}")
    return lines


# ---- full ANSI mode -----------------------------------------------------------


def _box(lines: List[str], width: int = BOX_WIDTH) -> str:
    top = "╔" + "═" * (width + 2) + "╗"
    bottom = "╚" + "═" * (width + 2) + "╝"
    body = ["║ " + line.ljust(width) + " ║" for line in lines]
    return "\n".join([top, "║" + " " * (width + 2) + "║"] + body + ["║" + " " * (width + 2) + "║", bottom])


def _section_header_full(title: str, emoji: str) -> str:
    return f"\n{'═' * 80}\n  {emoji} {title}\n{'═' * 80}"


def render_full(data: Dict[str, Any]) -> str:
    lines = [_box(_banner_lines(data)), "", f"   {_live_now_line(data)}"]

    lines.append(_section_header_full("EXECUTIVE SUMMARY", "📊"))
    lines.append(f"\n   {'Metric':<22} {'Current':>12} {'Previous':>12} {'Change':>12}")
    lines.append(f"   {'─' * 60}")
    for row in _exec_summary_rows(data):
        lines.append(f"   {row['label']:<22} {row['current_str']:>12} {row['previous_str']:>12} {row['change']:>12}")

    lines.append("\n   📈 User Activity:")
    for activity_line in _activity_lines(data):
        lines.append(f"      {activity_line}")

    lines.append(_section_header_full("HEALTH DASHBOARD", "🏥"))
    health = data["health"]
    for label, score in _sorted_scores(health["scores"]):
        if score is None:
            lines.append(f"   ⏳ {label:<20} (no data yet — coming in R2)")
        else:
            lines.append(f"   {_status_icon(score)} {label:<20} {bar(score, 100, 25)} {score:>3}/100")
    lines.append(f"\n   {'═' * 50}")
    overall = health["overall"]
    overall_str = f"{overall}/100" if overall is not None else "N/A"
    lines.append(f"   🎯 OVERALL SCORE: {overall_str} (Grade {health['grade']})")

    return "\n".join(lines)


# ---- telegram mode (width-safe, no box-art) -----------------------------------


def _section_header_telegram(title: str, emoji: str) -> str:
    return f"\n{emoji} {title}"


def render_telegram(data: Dict[str, Any]) -> str:
    lines = list(_banner_lines(data))
    lines.append("")
    lines.append(_live_now_line(data))

    lines.append(_section_header_telegram("EXECUTIVE SUMMARY", "📊"))
    for row in _exec_summary_rows(data):
        prev = "" if row["previous_str"] == "—" else f" (prev {row['previous_str']})"
        lines.append(f"{row['label']}: {row['current_str']}{prev} {row['change']}")

    lines.append("\n📈 User Activity:")
    for activity_line in _activity_lines(data):
        lines.append(activity_line)

    lines.append(_section_header_telegram("HEALTH DASHBOARD", "🏥"))
    health = data["health"]
    for label, score in _sorted_scores(health["scores"]):
        if score is None:
            lines.append(f"⏳ {label}: no data yet")
        else:
            lines.append(f"{_status_icon(score)} {label}: {score}/100")
    overall = health["overall"]
    overall_str = f"{overall}/100" if overall is not None else "N/A"
    lines.append(f"🎯 OVERALL: {overall_str} (Grade {health['grade']})")

    return "\n".join(lines)


# ---- json mode -----------------------------------------------------------------


def render_json(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "property": data["property"],
        "days": data["days"],
        "generated_at": data["generated_at"],
        "live_now": dict(data["realtime"]),
        "executive_summary": {
            "current": dict(data["executive"]["current"]),
            "previous": dict(data["executive"]["previous"]),
        },
        "user_activity": dict(data["activity"]),
        "health": {
            "scores": dict(data["health"]["scores"]),
            "overall": data["health"]["overall"],
            "grade": data["health"]["grade"],
        },
    }


# ---- dispatcher ------------------------------------------------------------------

_RENDERERS = {"full": render_full, "telegram": render_telegram, "json": render_json}


def render(data: Dict[str, Any], mode: str = "full"):
    try:
        renderer = _RENDERERS[mode]
    except KeyError:
        raise ValueError(f"unknown render mode '{mode}' — expected one of {sorted(_RENDERERS)}")
    return renderer(data)
