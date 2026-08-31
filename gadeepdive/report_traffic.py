"""Rendering for PART 1 §5 ACQUISITION and §6 GEOGRAPHY. Data in, string out
— no I/O, no clock. Mirrors `report.py`'s full/telegram split.
"""

from typing import Any, Dict

from .format import code_block, fixed_row, fmt_num, fmt_pct, section_header_full, section_header_telegram, star_string

FIRST_TOUCH_DISPLAY_LIMIT = 8
GEOGRAPHY_DISPLAY_LIMIT = 10
FIRST_TOUCH_TELEGRAM_LIMIT = 7
LANGUAGES_TELEGRAM_LIMIT = 6

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
        rows = [fixed_row([("Channel", 8, "l"), ("Sess", 5, "r"), ("Shr%", 4, "r"), ("Eng%", 4, "r"), ("Bnc%", 4, "r")])]
        for c in channels:
            rows.append(
                fixed_row(
                    [
                        (c["name"], 8, "l"),
                        (fmt_num(c["sessions"]), 5, "r"),
                        (fmt_pct(c["share"], 0), 4, "r"),
                        (fmt_pct(c["engaged_pct"], 0), 4, "r"),
                        (fmt_pct(c["bounce_pct"], 0), 4, "r"),
                    ]
                )
            )
        lines.append(code_block(rows))

    top_referrer = acquisition.get("top_referrer")
    lines.append(
        f"Top Referrer: {top_referrer['source_medium']} — {fmt_num(top_referrer['sessions'])} sessions"
        if top_referrer
        else "Top Referrer: no referral traffic"
    )

    first_touch = acquisition.get("first_touch", [])
    if not first_touch:
        lines.append("First-Touch Attribution: no data")
    else:
        lines.append("First-Touch Attribution:")
        rows = [fixed_row([("Source/Medium", 14, "l"), ("Sess", 5, "r"), ("Shr%", 4, "r")])]
        for ft in first_touch[:FIRST_TOUCH_TELEGRAM_LIMIT]:
            rows.append(
                fixed_row(
                    [
                        (f"{ft['source']}/{ft['medium']}", 14, "l"),
                        (fmt_num(ft["sessions"]), 5, "r"),
                        (fmt_pct(ft["share"], 0), 4, "r"),
                    ]
                )
            )
        lines.append(code_block(rows))

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
        rows = [fixed_row([("Country", 8, "l"), ("Sess", 5, "r"), ("Shr%", 4, "r"), ("Stars", 5, "l")])]
        for c in countries[:GEOGRAPHY_DISPLAY_LIMIT]:
            rows.append(
                fixed_row(
                    [
                        (c["name"], 8, "l"),
                        (fmt_num(c["sessions"]), 5, "r"),
                        (fmt_pct(c["share"], 0), 4, "r"),
                        (star_string(c["stars"]), 5, "l"),
                    ]
                )
            )
        lines.append(code_block(rows))

    languages = geography.get("languages", [])
    if not languages:
        lines.append("Languages: no language data")
    else:
        lines.append("Languages:")
        rows = [fixed_row([("Lang", 10, "l"), ("Sess", 5, "r"), ("Shr%", 4, "r")])]
        for lang in languages[:LANGUAGES_TELEGRAM_LIMIT]:
            rows.append(fixed_row([(lang["name"], 10, "l"), (fmt_num(lang["sessions"]), 5, "r"), (fmt_pct(lang["share"], 0), 4, "r")]))
        lines.append(code_block(rows))

    return "\n".join(lines)
