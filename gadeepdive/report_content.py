"""Rendering for PART 1 §7 CONTENT and §8 USER SEGMENTS. Data in, string out
— no I/O, no clock. Mirrors `report.py`'s full/telegram split.
"""

from typing import Any, Dict

from .format import bar, code_block, fixed_row, fmt_num, fmt_pct, section_header_full, section_header_telegram

TRENDING_TELEGRAM_LIMIT = 5
PROBLEM_PAGES_TELEGRAM_LIMIT = 5

# ---- content ------------------------------------------------------------------------


def content_full(data: Dict[str, Any]) -> str:
    content = data.get("content", {})
    sections = content.get("sections", [])
    lines = [section_header_full("CONTENT", "📄")]

    if not sections:
        lines.append("\n   no content data")
    else:
        lines.append(f"\n   {'Section':<18} {'Views':>10} {'Users':>10} {'Engage':>9} {'Pages':>7}")
        lines.append(f"   {'─' * 60}")
        for s in sections:
            lines.append(
                f"   {s['section']:<18} {fmt_num(s['views']):>10} {fmt_num(s['users']):>10} "
                f"{fmt_pct(s['engagement_pct']):>9} {s['page_count']:>7}"
            )

    trending = content.get("trending_up", [])
    lines.append("\n   🔥 Trending Up:")
    if not trending:
        lines.append("      no WoW gainers")
    else:
        for t in trending[:5]:
            lines.append(f"      {t['path']:<30} +{t['pct_change'] * 100:.0f}%")

    problems = content.get("problem_pages", [])
    lines.append("\n   🚨 Problem Pages:")
    if not problems:
        lines.append("      none")
    else:
        for p in problems[:5]:
            lines.append(f"      {p['path']:<30} {fmt_pct(p['bounce_pct'])} bounce")

    return "\n".join(lines)


def content_telegram(data: Dict[str, Any]) -> str:
    content = data.get("content", {})
    sections = content.get("sections", [])
    lines = [section_header_telegram("CONTENT", "📄")]

    if not sections:
        lines.append("no content data")
    else:
        rows = [fixed_row([("Section", 8, "l"), ("Views", 6, "r"), ("Users", 6, "r"), ("Eng%", 4, "r")])]
        for s in sections:
            rows.append(
                fixed_row(
                    [
                        (s["section"], 8, "l"),
                        (str(int(s["views"])), 6, "r"),
                        (str(int(s["users"])), 6, "r"),
                        (fmt_pct(s["engagement_pct"], 0), 4, "r"),
                    ]
                )
            )
        lines.append(code_block(rows))

    trending = content.get("trending_up", [])
    lines.append("🔥 Trending Up:")
    if not trending:
        lines.append("no WoW gainers")
    else:
        rows = [fixed_row([(t["path"], 20, "l"), (f"{t['pct_change'] * 100:+.0f}%", 8, "r")]) for t in trending[:TRENDING_TELEGRAM_LIMIT]]
        lines.append(code_block(rows))

    problems = content.get("problem_pages", [])
    lines.append("🚨 Problem Pages:")
    if not problems:
        lines.append("none")
    else:
        rows = [fixed_row([(p["path"], 22, "l"), (fmt_pct(p["bounce_pct"], 0), 6, "r")]) for p in problems[:PROBLEM_PAGES_TELEGRAM_LIMIT]]
        lines.append(code_block(rows))

    return "\n".join(lines)


# ---- user segments ----------------------------------------------------------------


def user_segments_full(data: Dict[str, Any]) -> str:
    segments = data.get("segments", {})
    new_vs_returning = segments.get("new_vs_returning", [])
    lines = [section_header_full("USER SEGMENTS", "👤")]

    if not new_vs_returning:
        lines.append("\n   no segment data")
    else:
        lines.append(f"\n   {'Segment':<14} {'Sessions':>10} {'Engage':>9}")
        lines.append(f"   {'─' * 40}")
        for s in new_vs_returning:
            lines.append(f"   {s['segment']:<14} {fmt_num(s['sessions']):>10} {fmt_pct(s['engagement_pct']):>9}")

    by_device = segments.get("by_device", [])
    lines.append("\n   By Device:")
    if not by_device:
        lines.append("      no device data")
    else:
        for d in by_device:
            lines.append(f"      {d['device']:<10} {bar(d['share'] * 100, 100, 20)} {fmt_pct(d['share'])}")

    return "\n".join(lines)


def user_segments_telegram(data: Dict[str, Any]) -> str:
    segments = data.get("segments", {})
    new_vs_returning = segments.get("new_vs_returning", [])
    lines = [section_header_telegram("USER SEGMENTS", "👤")]

    if not new_vs_returning:
        lines.append("no segment data")
    else:
        rows = [fixed_row([("Segment", 10, "l"), ("Sess", 6, "r"), ("Eng%", 5, "r")])]
        for s in new_vs_returning:
            rows.append(fixed_row([(s["segment"], 10, "l"), (fmt_num(s["sessions"]), 6, "r"), (fmt_pct(s["engagement_pct"], 0), 5, "r")]))
        lines.append(code_block(rows))

    by_device = segments.get("by_device", [])
    if not by_device:
        lines.append("By Device: no device data")
    else:
        lines.append("By Device:")
        rows = [fixed_row([("Device", 10, "l"), ("Sess", 6, "r"), ("Shr%", 5, "r")])]
        for d in by_device:
            rows.append(fixed_row([(d["device"], 10, "l"), (fmt_num(d["sessions"]), 6, "r"), (fmt_pct(d["share"], 0), 5, "r")]))
        lines.append(code_block(rows))

    return "\n".join(lines)
