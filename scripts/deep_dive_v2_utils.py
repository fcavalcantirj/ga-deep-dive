"""
GA4 DEEP DIVE v2 — UTILITIES
Small formatting/number-coercion helpers shared across the v2 CLI.
"""

# ============================================================================
# UTILITIES
# ============================================================================

def safe_int(val) -> int:
    try:
        return int(float(val))
    except:
        return 0

def safe_float(val) -> float:
    try:
        return float(val)
    except:
        return 0.0

def pct(val) -> str:
    """Format as percentage."""
    return f"{safe_float(val)*100:.1f}%"

def dur(seconds) -> str:
    """Format duration nicely."""
    s = safe_float(seconds)
    if s < 60:
        return f"{s:.0f}s"
    elif s < 3600:
        return f"{s/60:.1f}m"
    else:
        return f"{s/3600:.1f}h"

def delta(current, previous) -> str:
    """Format change with arrow."""
    if previous == 0:
        return "—"
    change = ((current - previous) / previous) * 100
    if change > 0:
        return f"↑{change:.1f}%"
    elif change < 0:
        return f"↓{abs(change):.1f}%"
    return "→0%"

def score_bar(score: int, width: int = 20) -> str:
    filled = int(score / 100 * width)
    return '█' * filled + '░' * (width - filled)

def section(title: str):
    """Print section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)

def subsection(title: str):
    print(f"\n  ── {title} ──")
