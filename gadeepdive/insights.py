"""§12 ACTIONABLE INSIGHTS — rule-based, pure over already-fetched/computed
data (acquisition, geography, content, activity, health, executive). No
backend calls of its own; this is the last step before rendering.

Each insight is `{"icon", "message", "action"}`. Rules fire independently and
are additive — zero, some, or all of them may appear in the output.
"""

from typing import Any, Dict, List

DOMINANT_CHANNEL_SHARE_THRESHOLD = 0.6
LOW_STICKINESS_DAU_PER_MAU_THRESHOLD = 0.1
STRONG_GROWTH_SCORE_THRESHOLD = 80


def _dominant_channel_insight(acquisition: Dict[str, Any]) -> List[Dict[str, str]]:
    channels = acquisition.get("channels", [])
    if not channels:
        return []
    top = channels[0]
    if top.get("share", 0) <= DOMINANT_CHANNEL_SHARE_THRESHOLD:
        return []
    return [
        {
            "icon": "🔴",
            "message": f"{top['name']} drives {top['share'] * 100:.0f}% of sessions — single point of failure",
            "action": "Diversify acquisition channels",
        }
    ]


def _low_stickiness_insight(activity: Dict[str, Any]) -> List[Dict[str, str]]:
    dau_per_mau = activity.get("dauPerMau")
    if dau_per_mau is None or dau_per_mau >= LOW_STICKINESS_DAU_PER_MAU_THRESHOLD:
        return []
    return [
        {
            "icon": "🔴",
            "message": f"Low stickiness: DAU/MAU is only {dau_per_mau * 100:.1f}%",
            "action": "Run retention campaigns (email, push, re-engagement flows)",
        }
    ]


def _problem_page_insight(content: Dict[str, Any]) -> List[Dict[str, str]]:
    problem_pages = content.get("problem_pages", [])
    if not problem_pages:
        return []
    worst = problem_pages[0]
    suffix = f" ({len(problem_pages)} pages affected)" if len(problem_pages) > 1 else ""
    return [
        {
            "icon": "🚨",
            "message": f"{worst['path']} has a {worst['bounce_pct'] * 100:.0f}% bounce rate{suffix}",
            "action": f"Fix landing page {worst['path']}",
        }
    ]


def _strong_growth_insight(health: Dict[str, Any], executive: Dict[str, Any], acquisition: Dict[str, Any]) -> List[Dict[str, str]]:
    growth_score = health.get("scores", {}).get("Growth")
    if growth_score is None or growth_score <= STRONG_GROWTH_SCORE_THRESHOLD:
        return []
    current = executive.get("current", {}).get("sessions", 0) or 0
    previous = executive.get("previous", {}).get("sessions", 0) or 0
    pct_change = ((current - previous) / previous * 100) if previous else 0
    channels = acquisition.get("channels", [])
    top_channel = channels[0]["name"] if channels else "your top channel"
    return [
        {
            "icon": "🟢",
            "message": f"Sessions up {pct_change:.0f}% WoW",
            "action": f"Double down on {top_channel}",
        }
    ]


def _top_geo_insight(geography: Dict[str, Any]) -> List[Dict[str, str]]:
    countries = geography.get("countries", [])
    if not countries:
        return []
    best = max(countries, key=lambda c: c.get("stars", 0))
    if best.get("stars", 0) < 4:
        return []
    return [
        {
            "icon": "🟢",
            "message": f"{best['name']} has the highest engagement quality ({best['stars']}★)",
            "action": f"Consider localization for {best['name']}",
        }
    ]


def compute(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Assemble the ordered ACTIONABLE INSIGHTS list from already-fetched sections."""
    insights: List[Dict[str, str]] = []
    insights += _dominant_channel_insight(data.get("acquisition", {}))
    insights += _low_stickiness_insight(data.get("activity", {}))
    insights += _problem_page_insight(data.get("content", {}))
    insights += _strong_growth_insight(data.get("health", {}), data.get("executive", {}), data.get("acquisition", {}))
    insights += _top_geo_insight(data.get("geography", {}))
    return insights
