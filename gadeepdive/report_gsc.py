"""Rendering for the GSC (Google Search Console) add-on section. Data in,
string out — no I/O, no clock. Mirrors `report.py`'s full/telegram split.
Returns "" (omitted entirely) when the section was suppressed via
`--no-gsc`; shows a graceful "no site configured" line when the property
has no `gsc_site` registered.
"""

from typing import Any, Dict

from .format import fmt_num, fmt_pct, section_header_full, section_header_telegram

TOP_QUERIES_DISPLAY_LIMIT = 10


def gsc_full(data: Dict[str, Any]) -> str:
    gsc = data.get("gsc")
    if gsc is None:
        return ""

    lines = [section_header_full("SEARCH CONSOLE", "🌐")]
    if not gsc.get("available"):
        lines.append(f"\n   No Search Console site configured for {data.get('property', '')}")
        return "\n".join(lines)

    totals = gsc.get("totals", {})
    lines.append(
        f"\n   Clicks: {fmt_num(totals.get('clicks', 0))}   Impressions: {fmt_num(totals.get('impressions', 0))}   "
        f"CTR: {fmt_pct(totals.get('ctr', 0))}   Avg Position: {totals.get('avg_position', 0):.1f}"
    )

    top_queries = gsc.get("top_queries", [])
    lines.append("\n   Top Queries:")
    if not top_queries:
        lines.append("      no query data")
    else:
        lines.append(f"      {'Query':<30} {'Clicks':>8} {'Impr':>10} {'CTR':>8} {'Pos':>6}")
        lines.append(f"      {'─' * 64}")
        for q in top_queries[:TOP_QUERIES_DISPLAY_LIMIT]:
            lines.append(
                f"      {q['query']:<30} {fmt_num(q['clicks']):>8} {fmt_num(q['impressions']):>10} "
                f"{fmt_pct(q['ctr']):>8} {q['position']:>6.1f}"
            )

    striking = gsc.get("striking_distance", [])
    lines.append("\n   🎯 Striking Distance (quick wins):")
    if not striking:
        lines.append("      none")
    else:
        for q in striking:
            lines.append(f"      {q['query']:<30} pos {q['position']:.1f}  {fmt_num(q['impressions'])} impr  {fmt_pct(q['ctr'])} CTR")

    return "\n".join(lines)


def gsc_telegram(data: Dict[str, Any]) -> str:
    gsc = data.get("gsc")
    if gsc is None:
        return ""

    lines = [section_header_telegram("SEARCH CONSOLE", "🌐")]
    if not gsc.get("available"):
        lines.append(f"No Search Console site configured for {data.get('property', '')}")
        return "\n".join(lines)

    totals = gsc.get("totals", {})
    lines.append(
        f"Clicks: {fmt_num(totals.get('clicks', 0))}  Impressions: {fmt_num(totals.get('impressions', 0))}  "
        f"CTR: {fmt_pct(totals.get('ctr', 0))}  Avg Pos: {totals.get('avg_position', 0):.1f}"
    )

    top_queries = gsc.get("top_queries", [])
    if top_queries:
        lines.append("Top Queries:")
        for q in top_queries[:TOP_QUERIES_DISPLAY_LIMIT]:
            lines.append(f"{q['query']}: {fmt_num(q['clicks'])} clicks, pos {q['position']:.1f}")

    striking = gsc.get("striking_distance", [])
    if striking:
        lines.append("🎯 Striking Distance:")
        for q in striking:
            lines.append(f"{q['query']}: pos {q['position']:.1f}, {fmt_num(q['impressions'])} impr, {fmt_pct(q['ctr'])} CTR")

    return "\n".join(lines)
