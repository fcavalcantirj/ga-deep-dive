"""Pure 0-100 health-score calculators (PART 1 §4 HEALTH DASHBOARD).

All 7 scores are wired with real formulas, each a pure function of its
already-fetched §5-11 section data. A score falls back to a neutral 50 only
when its section returned no rows at all (e.g. a property with no acquisition
data yet) — never `None` past R1.
"""

from typing import Any, Dict, Optional

_GROWTH_METRICS = ["sessions", "activeUsers", "newUsers", "engagedSessions"]
_NEUTRAL_SCORE = 50


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


def content_score(content: Optional[Dict[str, Any]]) -> int:
    """Content, from the problem-page ratio (lower is better) and average
    section engagement (higher is better), each weighted 50%."""
    content = content or {}
    sections = content.get("sections") or []
    if not sections:
        return _NEUTRAL_SCORE

    avg_engagement = sum(float(s.get("engagement_pct", 0) or 0) for s in sections) / len(sections)
    total_pages = sum(int(s.get("page_count", 0) or 0) for s in sections) or 1
    problem_ratio = min(1.0, len(content.get("problem_pages") or []) / total_pages)

    return max(0, min(100, round((0.5 * (1 - problem_ratio) + 0.5 * avg_engagement) * 100)))


def mobile_score(segments: Optional[Dict[str, Any]]) -> int:
    """Mobile, from mobile's share of sessions and mobile engagement rate,
    each weighted 50%."""
    by_device = (segments or {}).get("by_device") or []
    mobile = next((d for d in by_device if str(d.get("device", "")).lower() == "mobile"), None)
    if mobile is None:
        return _NEUTRAL_SCORE

    share = float(mobile.get("share", 0) or 0)
    engagement = float(mobile.get("engagement_pct", 0) or 0)
    return max(0, min(100, round((0.5 * share + 0.5 * engagement) * 100)))


def geo_diversity_score(geography: Optional[Dict[str, Any]]) -> int:
    """Geo Diversity, from country concentration: a lower top-country share
    of sessions means a more geographically diverse audience."""
    countries = (geography or {}).get("countries") or []
    if not countries:
        return _NEUTRAL_SCORE

    top_share = float(countries[0].get("share", 0) or 0)
    return max(0, min(100, round((1 - top_share) * 100)))


def traffic_diversity_score(acquisition: Optional[Dict[str, Any]]) -> int:
    """Traffic Diversity, from channel concentration: a lower top-channel
    share of sessions means less single-channel dependency risk."""
    channels = (acquisition or {}).get("channels") or []
    if not channels:
        return _NEUTRAL_SCORE

    top_share = float(channels[0].get("share", 0) or 0)
    return max(0, min(100, round((1 - top_share) * 100)))


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


def compute_dashboard(
    executive: Dict[str, Any],
    activity: Dict[str, Any],
    acquisition: Optional[Dict[str, Any]] = None,
    geography: Optional[Dict[str, Any]] = None,
    content: Optional[Dict[str, Any]] = None,
    segments: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble the 7-score HEALTH DASHBOARD from fetched §3, §5-8 data."""
    current = executive.get("current", {})
    previous = executive.get("previous", {})

    scores = {
        "Growth": growth_score(current, previous),
        "Content": content_score(content),
        "Engagement": engagement_score(current),
        "Mobile": mobile_score(segments),
        "Geo Diversity": geo_diversity_score(geography),
        "Retention": retention_score(activity),
        "Traffic Diversity": traffic_diversity_score(acquisition),
    }

    available = [v for v in scores.values() if v is not None]
    overall = round(sum(available) / len(available)) if available else None

    return {"scores": scores, "overall": overall, "grade": grade_for(overall)}
