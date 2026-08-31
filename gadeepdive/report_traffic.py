"""Rendering for PART 1 §5 ACQUISITION and §6 GEOGRAPHY. Data in, string out
— no I/O, no clock. Mirrors `report.py`'s full/telegram split.
"""

from typing import Any, Dict

from .format import fmt_num, fmt_pct, section_header_full, section_header_telegram, star_string

FIRST_TOUCH_DISPLAY_LIMIT = 8
GEOGRAPHY_DISPLAY_LIMIT = 10

# ---- acquisition ------------------------------------------------------------------


def acquisition_full(data: Dict[str, Any]) -> str:
    acquisition = data.get("acquisition", {})
    channels = acquisition.get("channels", [])
    lines = [section_header_full("ACQUISITION", "🚦")]

    if not channels:
        lines.append("\n   no acquisition data")
    else:
        lines.append(f"\n   {'Channel':<18} {'Sessions':>10} {'Share':>8} {'Engaged':>9} {'Bounce':>8} {'Dur':>8}")
        lines.append(f"   {'─' * 65}")
        for c in channels:
            lines.append(
                f"   {c['name']:<18} {fmt_num(c['sessions']):>10} {fmt_pct(c['share']):>8} "
                f"{fmt_pct(c['engaged_pct']):>9} {fmt_pct(c['bounce_pct']):>8} {c['avg_duration']:>7.0f}s"
            )

    top_referrer = acquisition.get("top_referrer")
    lines.append("\n   Top Referrer:")
    lines.append(
        f"      {top_referrer['source_medium']} — {fmt_num(top_referrer['sessions'])} sessions"
        if top_referrer
        else "      no referral traffic"
    )

    first_touch = acquisition.get("first_touch", [])
    lines.append("\n   First-Touch Attribution:")
    if not first_touch:
        lines.append("      no first-touch data")
    else:
        for ft in first_touch[:FIRST_TOUCH_DISPLAY_LIMIT]:
            lines.append(f"      {ft['source']} / {ft['medium']:<12} {fmt_num(ft['sessions']):>8}  {fmt_pct(ft['share'])}")

    return "\n".join(lines)


def acquisition_telegram(data: Dict[str, Any]) -> str:
    acquisition = data.get("acquisition", {})
    channels = acquisition.get("channels", [])
    lines = [section_header_telegram("ACQUISITION", "🚦")]

    if not channels:
        lines.append("no acquisition data")
    else:
        for c in channels:
            lines.append(f"{c['name']}: {fmt_num(c['sessions'])} ({fmt_pct(c['share'])}) engaged {fmt_pct(c['engaged_pct'])}")

    top_referrer = acquisition.get("top_referrer")
    lines.append(
        f"Top Referrer: {top_referrer['source_medium']} ({fmt_num(top_referrer['sessions'])})"
        if top_referrer
        else "Top Referrer: none"
    )

    first_touch = acquisition.get("first_touch", [])
    if first_touch:
        lines.append("First-Touch:")
        for ft in first_touch[:FIRST_TOUCH_DISPLAY_LIMIT]:
            lines.append(f"{ft['source']}/{ft['medium']}: {fmt_num(ft['sessions'])} ({fmt_pct(ft['share'])})")

    return "\n".join(lines)


# ---- geography --------------------------------------------------------------------


def geography_full(data: Dict[str, Any]) -> str:
    geography = data.get("geography", {})
    countries = geography.get("countries", [])
    lines = [section_header_full("GEOGRAPHY", "🌍")]

    if not countries:
        lines.append("\n   no geography data")
    else:
        lines.append(f"\n   {'Country':<18} {'Sessions':>10} {'Share':>8} {'Engaged':>9} {'Quality':>9}")
        lines.append(f"   {'─' * 60}")
        for c in countries[:GEOGRAPHY_DISPLAY_LIMIT]:
            lines.append(
                f"   {c['name']:<18} {fmt_num(c['sessions']):>10} {fmt_pct(c['share']):>8} "
                f"{fmt_pct(c['engaged_pct']):>9} {star_string(c['stars']):>9}"
            )

    languages = geography.get("languages", [])
    lines.append("\n   Languages:")
    if not languages:
        lines.append("      no language data")
    else:
        for lang in languages[:5]:
            lines.append(f"      {lang['name']:<10} {fmt_num(lang['sessions']):>8}  {fmt_pct(lang['share'])}")

    return "\n".join(lines)


def geography_telegram(data: Dict[str, Any]) -> str:
    geography = data.get("geography", {})
    countries = geography.get("countries", [])
    lines = [section_header_telegram("GEOGRAPHY", "🌍")]

    if not countries:
        lines.append("no geography data")
    else:
        for c in countries[:GEOGRAPHY_DISPLAY_LIMIT]:
            lines.append(f"{c['name']}: {fmt_num(c['sessions'])} ({fmt_pct(c['share'])}) {star_string(c['stars'])}")

    languages = geography.get("languages", [])
    if languages:
        lines.append("Languages:")
        for lang in languages[:5]:
            lines.append(f"{lang['name']}: {fmt_num(lang['sessions'])} ({fmt_pct(lang['share'])})")

    return "\n".join(lines)
