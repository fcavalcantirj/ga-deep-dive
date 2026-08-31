"""Rendering for PART 1 §11 TECHNOLOGY and §12 ACTIONABLE INSIGHTS. Data in,
string out — no I/O, no clock. Mirrors `report.py`'s full/telegram split.
"""

from typing import Any, Dict

from .format import fmt_num, fmt_pct, section_header_full, section_header_telegram

# ---- technology -----------------------------------------------------------------------


def technology_full(data: Dict[str, Any]) -> str:
    technology = data.get("technology", {})
    browsers = technology.get("browsers", [])
    lines = [section_header_full("TECHNOLOGY", "💻")]

    if not browsers:
        lines.append("\n   no browser data")
    else:
        lines.append(f"\n   {'Browser':<16} {'Sessions':>10} {'Engaged':>9}")
        lines.append(f"   {'─' * 40}")
        for b in browsers:
            lines.append(f"   {b['name']:<16} {fmt_num(b['sessions']):>10} {fmt_pct(b['engaged_pct']):>9}")

    resolutions = technology.get("resolutions", [])
    lines.append("\n   Top Resolutions:")
    if not resolutions:
        lines.append("      no resolution data")
    else:
        for r in resolutions[:5]:
            lines.append(f"      {r['resolution']:<12} {fmt_num(r['sessions']):>8}")

    return "\n".join(lines)


def technology_telegram(data: Dict[str, Any]) -> str:
    technology = data.get("technology", {})
    browsers = technology.get("browsers", [])
    lines = [section_header_telegram("TECHNOLOGY", "💻")]

    if not browsers:
        lines.append("no browser data")
    else:
        for b in browsers:
            lines.append(f"{b['name']}: {fmt_num(b['sessions'])} ({fmt_pct(b['engaged_pct'])} engaged)")

    resolutions = technology.get("resolutions", [])
    if resolutions:
        lines.append("Top Resolutions:")
        for r in resolutions[:5]:
            lines.append(f"{r['resolution']}: {fmt_num(r['sessions'])}")

    return "\n".join(lines)


# ---- actionable insights ---------------------------------------------------------------


def insights_full(data: Dict[str, Any]) -> str:
    insights = data.get("insights", [])
    lines = [section_header_full("ACTIONABLE INSIGHTS", "💡")]

    if not insights:
        lines.append("\n   no insights — not enough data yet")
    else:
        for insight in insights:
            lines.append(f"\n   {insight['icon']} {insight['message']}")
            lines.append(f"      → {insight['action']}")

    return "\n".join(lines)


def insights_telegram(data: Dict[str, Any]) -> str:
    insights = data.get("insights", [])
    lines = [section_header_telegram("ACTIONABLE INSIGHTS", "💡")]

    if not insights:
        lines.append("no insights — not enough data yet")
    else:
        for insight in insights:
            lines.append(f"{insight['icon']} {insight['message']} → {insight['action']}")

    return "\n".join(lines)
