"""Pure rendering of PART 1 §1-4 (banner, LIVE NOW, EXECUTIVE SUMMARY, HEALTH
DASHBOARD). Data in, string (or dict, for json mode) out — no I/O, no clock.

Three render modes:
- "full": ANSI report with box-art banner (default).
- "telegram": width-safe condensed variant, no box-art.
- "json": the same data as a plain dict (no art at all).
"""

from typing import Any, Dict, List, Optional, Tuple

from . import report_activity, report_content, report_gsc, report_part2, report_tech, report_traffic
from .format import BOX_WIDTH, bar, box, delta_arrow, fmt_num, fmt_pct, fmt_value
from .format import part_label_full as _part_label_full
from .format import part_label_telegram as _part_label_telegram
from .format import section_header_full as _section_header_full
from .format import section_header_telegram as _section_header_telegram
from .format import sorted_scores as _sorted_scores
from .format import status_icon as _status_icon

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


# ---- section builders (mode-agnostic content, mode-specific formatting) -----


def _top_banner_lines(data: Dict[str, Any]) -> List[str]:
    return [
        f"🏴‍☠️ {data['property'].upper()} FULL ANALYTICS REPORT",
        f"Generated: {data['generated_at']}",
        f"Period: Last {data['days']} days",
    ]


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


def render_full(data: Dict[str, Any]) -> str:
    lines = list(_top_banner_lines(data))
    lines.append(_part_label_full("PART 1: EXECUTIVE SUMMARY (V3)"))
    lines.append(box(_banner_lines(data)))
    lines.append("")
    lines.append(f"   {_live_now_line(data)}")

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

    lines.append(report_traffic.acquisition_full(data))
    lines.append(report_traffic.geography_full(data))
    lines.append(report_content.content_full(data))
    lines.append(report_content.user_segments_full(data))
    lines.append(report_activity.events_full(data))
    lines.append(report_activity.time_patterns_full(data))
    lines.append(report_tech.technology_full(data))
    lines.append(report_tech.insights_full(data))

    lines.append(_part_label_full("PART 2: THE FULL MONTY (V4)"))
    lines.append(report_part2.scroll_depth_full(data))
    lines.append(report_part2.user_flow_full(data))
    lines.append(report_part2.audiences_full(data))
    lines.append(report_part2.hourly_performance_full(data))
    lines.append(report_part2.acquisition_over_time_full(data))
    lines.append(report_part2.mobile_devices_full(data))
    lines.append(report_part2.full_monty_complete_full(data))

    gsc_section = report_gsc.gsc_full(data)
    if gsc_section:
        lines.append(gsc_section)

    return "\n".join(lines)


# ---- telegram mode (width-safe, no box-art) -----------------------------------


def render_telegram(data: Dict[str, Any]) -> str:
    lines = list(_top_banner_lines(data))
    lines.append(_part_label_telegram("PART 1: EXECUTIVE SUMMARY (V3)"))
    lines += _banner_lines(data)
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

    lines.append(report_traffic.acquisition_telegram(data))
    lines.append(report_traffic.geography_telegram(data))
    lines.append(report_content.content_telegram(data))
    lines.append(report_content.user_segments_telegram(data))
    lines.append(report_activity.events_telegram(data))
    lines.append(report_activity.time_patterns_telegram(data))
    lines.append(report_tech.technology_telegram(data))
    lines.append(report_tech.insights_telegram(data))

    lines.append(_part_label_telegram("PART 2: THE FULL MONTY (V4)"))
    lines.append(report_part2.scroll_depth_telegram(data))
    lines.append(report_part2.user_flow_telegram(data))
    lines.append(report_part2.audiences_telegram(data))
    lines.append(report_part2.hourly_performance_telegram(data))
    lines.append(report_part2.acquisition_over_time_telegram(data))
    lines.append(report_part2.mobile_devices_telegram(data))
    lines.append(report_part2.full_monty_complete_telegram(data))

    gsc_section = report_gsc.gsc_telegram(data)
    if gsc_section:
        lines.append(gsc_section)

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
        "acquisition": data.get("acquisition", {}),
        "geography": data.get("geography", {}),
        "content": data.get("content", {}),
        "user_segments": data.get("segments", {}),
        "events": data.get("events", {}),
        "time_patterns": data.get("time_patterns", {}),
        "technology": data.get("technology", {}),
        "insights": data.get("insights", []),
        "part2": {
            "scroll_depth": data.get("scroll_depth", {}),
            "user_flow": data.get("user_flow", {}),
            "audiences": data.get("audiences", {}),
            "hourly_performance": data.get("hourly_performance", {}),
            "acquisition_over_time": data.get("acquisition_over_time", {}),
            "mobile_devices": data.get("mobile_devices", {}),
        },
        "gsc": data.get("gsc"),
    }


# ---- dispatcher ------------------------------------------------------------------

_RENDERERS = {"full": render_full, "telegram": render_telegram, "json": render_json}


def render(data: Dict[str, Any], mode: str = "full"):
    try:
        renderer = _RENDERERS[mode]
    except KeyError:
        raise ValueError(f"unknown render mode '{mode}' — expected one of {sorted(_RENDERERS)}")
    return renderer(data)
