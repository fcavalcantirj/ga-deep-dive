"""Rendering for PART 1 §9 EVENTS and §10 TIME PATTERNS. Data in, string out
— no I/O, no clock. Mirrors `report.py`'s full/telegram split.
"""

from typing import Any, Dict

from .format import bar, code_block, fixed_row, fmt_num, fmt_pct, section_header_full, section_header_telegram, sparkline_lines

EVENTS_DISPLAY_LIMIT = 15
EVENTS_TELEGRAM_LIMIT = 10

# ---- events -------------------------------------------------------------------------


def events_full(data: Dict[str, Any]) -> str:
    events = data.get("events", {}).get("events", [])
    lines = [section_header_full("EVENTS", "⚡")]

    if not events:
        lines.append("\n   no event data")
    else:
        lines.append(f"\n   {'Event':<24} {'Count':>10} {'Per User':>10}")
        lines.append(f"   {'─' * 48}")
        for e in events[:EVENTS_DISPLAY_LIMIT]:
            lines.append(f"   {e['name']:<24} {fmt_num(e['count']):>10} {e['per_user']:>10.2f}")

    return "\n".join(lines)


def events_telegram(data: Dict[str, Any]) -> str:
    events = data.get("events", {}).get("events", [])
    lines = [section_header_telegram("EVENTS", "⚡")]

    if not events:
        lines.append("no event data")
    else:
        rows = [fixed_row([("Event", 14, "l"), ("Count", 7, "r"), ("/User", 6, "r")])]
        for e in events[:EVENTS_TELEGRAM_LIMIT]:
            rows.append(fixed_row([(e["name"], 14, "l"), (fmt_num(e["count"]), 7, "r"), (f"{e['per_user']:.2f}", 6, "r")]))
        lines.append(code_block(rows))

    return "\n".join(lines)


# ---- time patterns --------------------------------------------------------------------


def time_patterns_full(data: Dict[str, Any]) -> str:
    time_patterns = data.get("time_patterns", {})
    day_of_week = time_patterns.get("day_of_week", [])
    lines = [section_header_full("TIME PATTERNS", "🕐")]

    if not day_of_week:
        lines.append("\n   no day-of-week data")
    else:
        max_sessions = max((d["sessions"] for d in day_of_week), default=0)
        for d in day_of_week:
            lines.append(
                f"   {d['day_name']:<10} {bar(d['sessions'], max_sessions, 20)} "
                f"{fmt_num(d['sessions']):>8}  engaged {d['engaged_pct'] * 100:.0f}%"
            )

    daily = time_patterns.get("daily", [])
    lines.append("\n   Last 7 Days:")
    if not daily:
        lines.append("      no daily data")
    else:
        for line in sparkline_lines(daily, "date", "sessions"):
            lines.append(f"      {line}")

    return "\n".join(lines)


def time_patterns_telegram(data: Dict[str, Any]) -> str:
    time_patterns = data.get("time_patterns", {})
    day_of_week = time_patterns.get("day_of_week", [])
    lines = [section_header_telegram("TIME PATTERNS", "🕐")]

    if not day_of_week:
        lines.append("no day-of-week data")
    else:
        rows = [fixed_row([("Day", 10, "l"), ("Sess", 6, "r"), ("Eng%", 5, "r")])]
        for d in day_of_week:
            rows.append(fixed_row([(d["day_name"], 10, "l"), (fmt_num(d["sessions"]), 6, "r"), (fmt_pct(d["engaged_pct"], 0), 5, "r")]))
        lines.append(code_block(rows))

    daily = time_patterns.get("daily", [])
    lines.append("Daily Sessions:")
    if not daily:
        lines.append("no daily data")
    else:
        rows = [fixed_row([("Date", 10, "l"), ("Sess", 8, "r")])]
        for d in daily:
            rows.append(fixed_row([(d["date"], 10, "l"), (fmt_num(d["sessions"]), 8, "r")]))
        lines.append(code_block(rows))

    return "\n".join(lines)
