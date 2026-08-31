"""Rendering for PART 1 §9 EVENTS and §10 TIME PATTERNS. Data in, string out
— no I/O, no clock. Mirrors `report.py`'s full/telegram split.
"""

from typing import Any, Dict

from .format import bar, fmt_num, section_header_full, section_header_telegram, sparkline_lines

EVENTS_DISPLAY_LIMIT = 15

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
        for e in events[:EVENTS_DISPLAY_LIMIT]:
            lines.append(f"{e['name']}: {fmt_num(e['count'])} ({e['per_user']:.2f}/user)")

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
        for d in day_of_week:
            lines.append(f"{d['day_name']}: {fmt_num(d['sessions'])} (engaged {d['engaged_pct'] * 100:.0f}%)")

    daily = time_patterns.get("daily", [])
    if daily:
        lines.append("Last 7 Days:")
        for line in sparkline_lines(daily, "date", "sessions"):
            lines.append(line)

    return "\n".join(lines)
