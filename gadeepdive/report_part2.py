"""Rendering for PART 2 §13-19: scroll depth, user flow entry points, GA4
audiences, hourly performance, acquisition over time, mobile devices, and
the closing FULL MONTY COMPLETE block. Data in, string out — no I/O, no
clock. Mirrors `report.py`'s full/telegram split.
"""

from typing import Any, Dict

from .format import bar, fmt_num, fmt_pct, section_header_full, section_header_telegram

ENTRY_POINTS_DISPLAY_LIMIT = 10
MOBILE_DEVICES_DISPLAY_LIMIT = 8

# ---- scroll depth -----------------------------------------------------------------


def scroll_depth_full(data: Dict[str, Any]) -> str:
    scroll = data.get("scroll_depth", {})
    lines = [section_header_full("SCROLL DEPTH", "📜")]

    if not scroll.get("total_events"):
        lines.append("\n   no scroll data")
    else:
        lines.append(f"\n   {'Depth':<10} {'Events':>10} {'Share':>8}")
        lines.append(f"   {'─' * 32}")
        for d in scroll.get("distribution", []):
            lines.append(f"   {d['depth'] + '%':<10} {fmt_num(d['count']):>10} {fmt_pct(d['share']):>8}")

    top_pages = scroll.get("top_pages", [])
    lines.append("\n   Page Completion Rates (reach 90%+ scroll):")
    if not top_pages:
        lines.append("      no page completion data")
    else:
        for p in top_pages[:5]:
            lines.append(f"      {p['path']:<30} {fmt_pct(p['completion_rate'])}")

    return "\n".join(lines)


def scroll_depth_telegram(data: Dict[str, Any]) -> str:
    scroll = data.get("scroll_depth", {})
    lines = [section_header_telegram("SCROLL DEPTH", "📜")]

    if not scroll.get("total_events"):
        lines.append("no scroll data")
    else:
        for d in scroll.get("distribution", []):
            lines.append(f"{d['depth']}%: {fmt_num(d['count'])} ({fmt_pct(d['share'])})")

    top_pages = scroll.get("top_pages", [])
    if top_pages:
        lines.append("Page Completion:")
        for p in top_pages[:5]:
            lines.append(f"{p['path']}: {fmt_pct(p['completion_rate'])}")

    return "\n".join(lines)


# ---- user flow entry points --------------------------------------------------------


def user_flow_full(data: Dict[str, Any]) -> str:
    entries = data.get("user_flow", {}).get("entries", [])
    lines = [section_header_full("USER FLOW — ENTRY POINTS", "🚪")]

    if not entries:
        lines.append("\n   no entry point data")
    else:
        lines.append(f"\n   {'Landing Page':<32} {'Entries':>10} {'Bounce':>8}")
        lines.append(f"   {'─' * 54}")
        for e in entries[:ENTRY_POINTS_DISPLAY_LIMIT]:
            lines.append(f"   {e['path']:<32} {fmt_num(e['entries']):>10} {fmt_pct(e['bounce_pct']):>8}")

    return "\n".join(lines)


def user_flow_telegram(data: Dict[str, Any]) -> str:
    entries = data.get("user_flow", {}).get("entries", [])
    lines = [section_header_telegram("USER FLOW — ENTRY POINTS", "🚪")]

    if not entries:
        lines.append("no entry point data")
    else:
        for e in entries[:ENTRY_POINTS_DISPLAY_LIMIT]:
            lines.append(f"{e['path']}: {fmt_num(e['entries'])} entries ({fmt_pct(e['bounce_pct'])} bounce)")

    return "\n".join(lines)


# ---- ga4 audiences ------------------------------------------------------------------


def audiences_full(data: Dict[str, Any]) -> str:
    audience_list = data.get("audiences", {}).get("audiences", [])
    lines = [section_header_full("GA4 AUDIENCES", "🎯")]

    if not audience_list:
        lines.append("\n   No custom audiences configured")
    else:
        lines.append(f"\n   {'Audience':<28} {'Users':>8} {'Sessions':>10} {'Engage':>9}")
        lines.append(f"   {'─' * 58}")
        for a in audience_list:
            lines.append(f"   {a['name']:<28} {fmt_num(a['users']):>8} {fmt_num(a['sessions']):>10} {fmt_pct(a['engagement_pct']):>9}")

    return "\n".join(lines)


def audiences_telegram(data: Dict[str, Any]) -> str:
    audience_list = data.get("audiences", {}).get("audiences", [])
    lines = [section_header_telegram("GA4 AUDIENCES", "🎯")]

    if not audience_list:
        lines.append("No custom audiences configured")
    else:
        for a in audience_list:
            lines.append(f"{a['name']}: {fmt_num(a['users'])} users, {fmt_num(a['sessions'])} sessions ({fmt_pct(a['engagement_pct'])} engaged)")

    return "\n".join(lines)


# ---- hourly performance ------------------------------------------------------------


def hourly_performance_full(data: Dict[str, Any]) -> str:
    hourly = data.get("hourly_performance", {})
    hours = hourly.get("hours", [])
    best_hour = hourly.get("best_hour")
    lines = [section_header_full("HOURLY PERFORMANCE", "🕐")]

    if not hours:
        lines.append("\n   no hourly data")
    else:
        lines.append(f"\n   {'Hour':<8} {'Sessions':>10} {'Engaged':>9} {'Eng Rate':>10} {'Avg Dur':>10}")
        lines.append(f"   {'─' * 52}")
        for h in hours:
            marker = " ← BEST" if h["hour"] == best_hour else ""
            lines.append(
                f"   {h['hour']:02d}:00{'':<3} {fmt_num(h['sessions']):>10} {fmt_num(h['engaged']):>9} "
                f"{fmt_pct(h['engagement_rate']):>10} {h['avg_duration']:>8.0f}s{marker}"
            )

    return "\n".join(lines)


def hourly_performance_telegram(data: Dict[str, Any]) -> str:
    hourly = data.get("hourly_performance", {})
    hours = hourly.get("hours", [])
    best_hour = hourly.get("best_hour")
    lines = [section_header_telegram("HOURLY PERFORMANCE", "🕐")]

    if not hours:
        lines.append("no hourly data")
    else:
        for h in hours:
            marker = " ← BEST" if h["hour"] == best_hour else ""
            lines.append(f"{h['hour']:02d}:00 {fmt_num(h['sessions'])} sessions, {fmt_pct(h['engagement_rate'])} engaged{marker}")

    return "\n".join(lines)


# ---- acquisition over time ----------------------------------------------------------


def acquisition_over_time_full(data: Dict[str, Any]) -> str:
    daily = data.get("acquisition_over_time", {}).get("daily", [])
    lines = [section_header_full("ACQUISITION OVER TIME", "📅")]

    if not daily:
        lines.append("\n   no acquisition-over-time data")
    else:
        max_users = max((d["users"] for d in daily), default=0)
        for d in daily:
            lines.append(f"   {d['date']:<10} {bar(d['users'], max_users, 20)} {fmt_num(d['users']):>8}")

    return "\n".join(lines)


def acquisition_over_time_telegram(data: Dict[str, Any]) -> str:
    daily = data.get("acquisition_over_time", {}).get("daily", [])
    lines = [section_header_telegram("ACQUISITION OVER TIME", "📅")]

    if not daily:
        lines.append("no acquisition-over-time data")
    else:
        for d in daily:
            lines.append(f"{d['date']}: {fmt_num(d['users'])} users")

    return "\n".join(lines)


# ---- mobile devices -------------------------------------------------------------------


def mobile_devices_full(data: Dict[str, Any]) -> str:
    models = data.get("mobile_devices", {}).get("models", [])
    lines = [section_header_full("MOBILE DEVICES", "📱")]

    if not models:
        lines.append("\n   No mobile device data")
    else:
        lines.append(f"\n   {'Model':<28} {'Sessions':>10}")
        lines.append(f"   {'─' * 40}")
        for m in models[:MOBILE_DEVICES_DISPLAY_LIMIT]:
            lines.append(f"   {m['model']:<28} {fmt_num(m['sessions']):>10}")

    return "\n".join(lines)


def mobile_devices_telegram(data: Dict[str, Any]) -> str:
    models = data.get("mobile_devices", {}).get("models", [])
    lines = [section_header_telegram("MOBILE DEVICES", "📱")]

    if not models:
        lines.append("No mobile device data")
    else:
        for m in models[:MOBILE_DEVICES_DISPLAY_LIMIT]:
            lines.append(f"{m['model']}: {fmt_num(m['sessions'])} sessions")

    return "\n".join(lines)


# ---- full monty complete ---------------------------------------------------------------


def full_monty_complete_full(data: Dict[str, Any]) -> str:
    lines = [section_header_full("FULL MONTY COMPLETE", "✅")]
    lines.append(f"\n   Property: {data['property'].upper()}     Period: Last {data['days']} days")
    return "\n".join(lines)


def full_monty_complete_telegram(data: Dict[str, Any]) -> str:
    lines = [section_header_telegram("FULL MONTY COMPLETE", "✅")]
    lines.append(f"Property: {data['property'].upper()}  Period: Last {data['days']} days")
    return "\n".join(lines)
