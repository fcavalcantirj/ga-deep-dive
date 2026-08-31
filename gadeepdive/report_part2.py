"""Rendering for PART 2 §13-19: scroll depth, user flow entry points, GA4
audiences, hourly performance, acquisition over time, mobile devices, and
the closing FULL MONTY COMPLETE block. Data in, string out — no I/O, no
clock. Mirrors `report.py`'s full/telegram split.
"""

from typing import Any, Dict

from .format import bar, code_block, fixed_row, fmt_num, fmt_pct, section_header_full, section_header_telegram

ENTRY_POINTS_DISPLAY_LIMIT = 10
MOBILE_DEVICES_DISPLAY_LIMIT = 8
SCROLL_TOP_PAGES_TELEGRAM_LIMIT = 5
ENTRY_POINTS_TELEGRAM_LIMIT = 6
MOBILE_DEVICES_TELEGRAM_LIMIT = 8
PEAK_HOURS_TELEGRAM_LIMIT = 3

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
        lines.append(f"Total events: {fmt_num(scroll['total_events'])}")
        rows = [fixed_row([("Depth", 6, "l"), ("Count", 8, "r"), ("Shr%", 5, "r")])]
        for d in scroll.get("distribution", []):
            rows.append(fixed_row([(f"{d['depth']}%", 6, "l"), (fmt_num(d["count"]), 8, "r"), (fmt_pct(d["share"], 0), 5, "r")]))
        lines.append(code_block(rows))

    top_pages = scroll.get("top_pages", [])
    lines.append("Page Completion:")
    if not top_pages:
        lines.append("no page completion data")
    else:
        rows = [fixed_row([("Page", 20, "l"), ("Comp%", 6, "r")])]
        for p in top_pages[:SCROLL_TOP_PAGES_TELEGRAM_LIMIT]:
            rows.append(fixed_row([(p["path"], 20, "l"), (fmt_pct(p["completion_rate"], 0), 6, "r")]))
        lines.append(code_block(rows))

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
    lines = [section_header_telegram("ENTRY POINTS", "🚪")]

    if not entries:
        lines.append("no entry point data")
    else:
        rows = [fixed_row([("Landing", 16, "l"), ("Entr", 6, "r"), ("Bnc%", 5, "r")])]
        for e in entries[:ENTRY_POINTS_TELEGRAM_LIMIT]:
            rows.append(fixed_row([(e["path"], 16, "l"), (fmt_num(e["entries"]), 6, "r"), (fmt_pct(e["bounce_pct"], 0), 5, "r")]))
        lines.append(code_block(rows))

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
        lines.append("none configured")
    else:
        rows = [fixed_row([("Audience", 10, "l"), ("Users", 5, "r"), ("Sess", 6, "r"), ("Eng%", 4, "r")])]
        for a in audience_list:
            rows.append(
                fixed_row(
                    [
                        (a["name"], 10, "l"),
                        (fmt_num(a["users"]), 5, "r"),
                        (fmt_num(a["sessions"]), 6, "r"),
                        (fmt_pct(a["engagement_pct"], 0), 4, "r"),
                    ]
                )
            )
        lines.append(code_block(rows))

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
    """Telegram shows the top 3 hours by session volume — "Peak Hours" —
    rather than the full mode's all-24-hours-with-a-BEST-marker table."""
    hourly = data.get("hourly_performance", {})
    hours = hourly.get("hours", [])
    lines = [section_header_telegram("PEAK HOURS", "🕐")]

    if not hours:
        lines.append("no hourly data")
    else:
        top_hours = sorted(hours, key=lambda h: h["sessions"], reverse=True)[:PEAK_HOURS_TELEGRAM_LIMIT]
        rows = [fixed_row([("Hour", 6, "l"), ("Sess", 6, "r"), ("Eng%", 5, "r")])]
        for h in top_hours:
            rows.append(fixed_row([(f"{h['hour']:02d}:00", 6, "l"), (fmt_num(h["sessions"]), 6, "r"), (fmt_pct(h["engagement_rate"], 0), 5, "r")]))
        lines.append(code_block(rows))

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
        lines.append("no mobile device data")
    else:
        rows = [fixed_row([("Model", 20, "l"), ("Sessions", 8, "r")])]
        for m in models[:MOBILE_DEVICES_TELEGRAM_LIMIT]:
            rows.append(fixed_row([(m["model"], 20, "l"), (fmt_num(m["sessions"]), 8, "r")]))
        lines.append(code_block(rows))

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
