"""Shared, mode-agnostic rendering helpers used by `report.py` and the §5-12
`report_*.py` section renderers. Pure formatting only — no I/O, no clock, no
GA4-specific data shaping (that belongs in `fetch.py`).

Kept in its own leaf module (no imports from `report.py` or `report_*.py`)
so the section renderers can share these helpers without a circular import.
"""

from typing import Dict, List, Optional, Tuple

BOX_WIDTH = 78
TELEGRAM_WIDTH = 30


def fmt_num(n: float) -> str:
    n = float(n or 0)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(int(n))


def fmt_pct(value: float, decimals: int = 1) -> str:
    return f"{float(value or 0) * 100:.{decimals}f}%"


def fmt_value(value: float, kind: str) -> str:
    if kind == "pct":
        return fmt_pct(value)
    if kind == "duration":
        return f"{float(value or 0):.0f}s"
    if kind == "decimal":
        return f"{float(value or 0):.2f}"
    return fmt_num(value)


def delta_arrow(current: float, previous: Optional[float], reverse: bool = False) -> str:
    """WoW change indicator. `reverse=True` means down is good (e.g. bounce rate)."""
    current = float(current or 0)
    if not previous:
        return "NEW" if current > 0 else "—"
    change = (current - previous) / previous * 100
    if reverse:
        change = -change
    if change > 10:
        return f"🟢 +{change:.0f}%"
    if change > 0:
        return f"↑{change:.0f}%"
    if change < -10:
        return f"🔴 {change:.0f}%"
    if change < 0:
        return f"↓{abs(change):.0f}%"
    return "→"


def bar(value: float, max_value: float = 100, width: int = 20) -> str:
    if max_value == 0:
        return "░" * width
    filled = max(0, min(width, int(value / max_value * width)))
    return "█" * filled + "░" * (width - filled)


def status_icon(score: int) -> str:
    if score >= 80:
        return "✅"
    if score >= 60:
        return "⚠️"
    return "🔴"


def sorted_scores(scores: Dict[str, Optional[int]]) -> List[Tuple[str, Optional[int]]]:
    return sorted(scores.items(), key=lambda item: item[1] if item[1] is not None else -1, reverse=True)


def star_string(count: int, total: int = 5) -> str:
    """Render a 1-5 quality-star rating as `★★★☆☆`."""
    count = max(0, min(total, int(count)))
    return "★" * count + "☆" * (total - count)


def sparkline_lines(rows: List[Dict], label_key: str, value_key: str, width: int = 20) -> List[str]:
    """Bar-chart lines for a small time series, with `← PEAK` on the max row."""
    if not rows:
        return []
    values = [float(row.get(value_key, 0) or 0) for row in rows]
    max_value = max(values)
    peak_index = values.index(max_value)
    lines = []
    for i, row in enumerate(rows):
        marker = " ← PEAK" if i == peak_index else ""
        lines.append(f"{row[label_key]:<12} {bar(values[i], max_value, width)} {fmt_num(values[i]):>8}{marker}")
    return lines


def box(lines: List[str], width: int = BOX_WIDTH) -> str:
    top = "╔" + "═" * (width + 2) + "╗"
    bottom = "╚" + "═" * (width + 2) + "╝"
    body = ["║ " + line.ljust(width) + " ║" for line in lines]
    return "\n".join([top, "║" + " " * (width + 2) + "║"] + body + ["║" + " " * (width + 2) + "║", bottom])


def section_header_full(title: str, emoji: str) -> str:
    return f"\n{'═' * 80}\n  {emoji} {title}\n{'═' * 80}"


def section_header_telegram(title: str, emoji: str) -> str:
    return f"\n**{emoji} {title}**"


def part_label_full(title: str) -> str:
    return f"\n{'▓' * 80}\n  {title}\n{'▓' * 80}"


# ---- telegram phone-width helpers (max 30 cols, code blocks for tables/bars) -------


def truncate(text, width: int) -> str:
    """Shorten `text` to fit `width` columns, marking the cut with `…`."""
    text = str(text)
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "…"


def fixed_cell(text, width: int, align: str = "l") -> str:
    """Truncate `text` to `width` then pad it so a row's total width is
    deterministic regardless of the source field's real length."""
    cell = truncate(text, width)
    return cell.rjust(width) if align == "r" else cell.ljust(width)


def fixed_row(cells: List[Tuple]) -> str:
    """Build one code-block table row from `(text, width, align)` cells,
    space-joined. Numbers are never truncated (only labels are) — pick
    widths generous enough for the values a section can produce."""
    return " ".join(fixed_cell(text, width, align) for text, width, align in cells).rstrip()


def code_block(lines: List[str]) -> str:
    """Wrap pre-formatted monospace `lines` (tables, bar charts) in a
    Markdown code fence so columns stay aligned on a phone."""
    body = "\n".join(lines)
    return f"```\n{body}\n```"


def telegram_delta(current: float, previous: Optional[float], reverse: bool = False) -> str:
    """WoW change indicator for telegram mode: `🟢+231%` / `🔴-12%` — every
    non-NEW change is colored by sign, no "mild change" middle ground like
    `delta_arrow`'s full-mode ↑/↓. `reverse=True` means down is good."""
    current = float(current or 0)
    if not previous:
        return "NEW" if current > 0 else "—"
    change = (current - previous) / previous * 100
    if reverse:
        change = -change
    icon = "🟢" if change >= 0 else "🔴"
    return f"{icon}{change:+.0f}%"
