"""Pure 0-100 health-score calculators (PART 1 §4 HEALTH DASHBOARD).

Engagement, Growth and Retention are wired with real formulas. Content,
Mobile, Geo Diversity and Traffic Diversity are documented stubs returning
`None` until their source data (§7/8 content, §11 tech/mobile, §6 geography,
§5 acquisition) lands in R2.
"""

from typing import Any, Dict, Optional

_GROWTH_METRICS = ["sessions", "activeUsers", "newUsers", "engagedSessions"]


def engagement_score(current: Dict[str, Any]) -> int:
    """Engagement, from engagementRate (0-1 fraction) scaled to 0-100."""
    rate = float(current.get("engagementRate", 0) or 0)
    return max(0, min(100, round(rate * 100)))


def growth_score(current: Dict[str, Any], previous: Dict[str, Any]) -> int:
    """Growth, from the average WoW delta across sessions/users/engagement."""
    deltas = []
    for key in _GROWTH_METRICS:
        prev_value = previous.get(key)
        if prev_value:
            curr_value = current.get(key, 0)
            deltas.append((curr_value - prev_value) / prev_value)

    if not previous or not deltas:
        has_current_activity = any(current.get(key, 0) for key in _GROWTH_METRICS)
        return 75 if has_current_activity else 50

    avg_delta = sum(deltas) / len(deltas)
    return max(0, min(100, round(50 + avg_delta * 100)))


def retention_score(activity: Dict[str, Any]) -> int:
    """Retention, from dauPerMau (20% dau/mau => 100)."""
    dau_per_mau = activity.get("dauPerMau")
    if dau_per_mau is None:
        dau = activity.get("active1DayUsers", 0) or 0
        mau = activity.get("active28DayUsers", 0) or 0
        dau_per_mau = (dau / mau) if mau else 0
    return max(0, min(100, round(float(dau_per_mau) * 500)))


def content_score(*_args, **_kwargs) -> Optional[int]:
    """Stub — needs §7 CONTENT data (R2). Returns None until wired."""
    return None


def mobile_score(*_args, **_kwargs) -> Optional[int]:
    """Stub — needs §11 TECHNOLOGY/mobile data (R2). Returns None until wired."""
    return None


def geo_diversity_score(*_args, **_kwargs) -> Optional[int]:
    """Stub — needs §6 GEOGRAPHY data (R2). Returns None until wired."""
    return None


def traffic_diversity_score(*_args, **_kwargs) -> Optional[int]:
    """Stub — needs §5 ACQUISITION data (R2). Returns None until wired."""
    return None


def grade_for(score: Optional[int]) -> str:
    if score is None:
        return "N/A"
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"


def compute_dashboard(executive: Dict[str, Any], activity: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble the 7-score HEALTH DASHBOARD from fetched §3 data."""
    current = executive.get("current", {})
    previous = executive.get("previous", {})

    scores = {
        "Growth": growth_score(current, previous),
        "Content": content_score(),
        "Engagement": engagement_score(current),
        "Mobile": mobile_score(),
        "Geo Diversity": geo_diversity_score(),
        "Retention": retention_score(activity),
        "Traffic Diversity": traffic_diversity_score(),
    }

    available = [v for v in scores.values() if v is not None]
    overall = round(sum(available) / len(available)) if available else None

    return {"scores": scores, "overall": overall, "grade": grade_for(overall)}
