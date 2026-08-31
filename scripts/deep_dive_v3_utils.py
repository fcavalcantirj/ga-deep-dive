"""
GA4 DEEP DIVE v3 — UTILITIES
Small formatting/number-coercion helpers shared across the v3 CLI.
"""

from typing import List

# ============================================================================
# UTILITIES
# ============================================================================

def safe_int(val) -> int:
    try: return int(float(val))
    except: return 0

def safe_float(val) -> float:
    try: return float(val)
    except: return 0.0

def pct(val, decimals=1) -> str:
    return f"{safe_float(val)*100:.{decimals}f}%"

def fmt_num(n) -> str:
    n = safe_int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def delta_str(current, previous, reverse=False) -> str:
    if previous == 0: return "NEW" if current > 0 else "—"
    change = ((current - previous) / previous) * 100
    if reverse: change = -change  # For metrics where down is good (bounce rate)
    if change > 10: return f"🟢 +{change:.0f}%"
    elif change > 0: return f"↑{change:.0f}%"
    elif change < -10: return f"🔴 {change:.0f}%"
    elif change < 0: return f"↓{abs(change):.0f}%"
    return "→"

def bar(value, max_value, width=20) -> str:
    if max_value == 0: return "░" * width
    filled = int(value / max_value * width)
    return "█" * filled + "░" * (width - filled)

def sparkline(values: List[float]) -> str:
    if not values: return ""
    chars = "▁▂▃▄▅▆▇█"
    min_v, max_v = min(values), max(values)
    if max_v == min_v: return chars[4] * len(values)
    return "".join(chars[int((v - min_v) / (max_v - min_v) * 7)] for v in values)

def section(title: str, emoji: str = ""):
    print(f"\n{'═'*80}")
    print(f"  {emoji} {title}")
    print('═'*80)

def subsection(title: str):
    print(f"\n  ┌─ {title} {'─'*(70-len(title))}")
