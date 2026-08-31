#!/usr/bin/env python3
"""
GA4 DEEP DIVE v3 — THE OWNER'S WAR ROOM
Built for Solvr by Claudius 🏴‍☠️

This is what you ACTUALLY need to run a product:

1. COHORTS — Are users coming back? Week 1 vs Week 4 retention
2. FUNNELS — Where do users drop off? Visit → Join → API Key → Post
3. SEGMENTS — Power users vs casual, who's your 1%?
4. ATTRIBUTION — Which sources ACTUALLY convert?
5. TRENDS — What's hot? What's dying? Early warnings
6. GEOGRAPHY — Which countries are gold mines?
7. EVENTS — What do engaged users do differently?

Usage:
    python3 deep_dive_v3.py solvr
    python3 deep_dive_v3.py solvr --days 30 --output json
"""

import argparse
import json

from deep_dive_v3_analysis import (
    analyze_executive, analyze_acquisition_deep, analyze_geography_deep,
    analyze_content_deep, analyze_events_deep, analyze_user_segments,
    analyze_time_patterns, analyze_technology, calculate_health_scores
)
from deep_dive_v3_client import GA4
from deep_dive_v3_config import PROPERTIES
from deep_dive_v3_report import print_report, save_snapshot

# ============================================================================
# MAIN
# ============================================================================

def deep_dive(property_name: str, days: int = 30, output: str = "text"):
    """Run complete deep dive analysis."""

    property_id = PROPERTIES.get(property_name.lower(), property_name)
    is_solvr = property_name.lower() == "solvr"

    print(f"\n🔄 Analyzing {property_name}...")

    ga = GA4(property_id)

    # Collect all data
    data = {
        "realtime": ga.realtime(),
        "executive": analyze_executive(ga, days),
        "acquisition": analyze_acquisition_deep(ga, days),
        "geography": analyze_geography_deep(ga, days),
        "content": analyze_content_deep(ga, days, is_solvr=is_solvr),
        "events": analyze_events_deep(ga, days),
        "segments": analyze_user_segments(ga, days),
        "time": analyze_time_patterns(ga, days),
        "technology": analyze_technology(ga, days),
    }

    # Calculate scores
    data["scores"] = calculate_health_scores(data, days)

    # Output
    if output == "json":
        print(json.dumps(data, indent=2, default=str))
    else:
        print_report(data, property_name, days)
        save_snapshot(data, property_name, days)

    return data


def main():
    parser = argparse.ArgumentParser(description="GA4 Deep Dive v3 — Owner's War Room")
    parser.add_argument("property", nargs="?", help="Property name or ID")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--list", action="store_true")

    args = parser.parse_args()

    if args.list:
        print("\n📋 Properties:")
        for name, pid in PROPERTIES.items():
            print(f"   {name:<15} → {pid}")
        return

    if not args.property:
        parser.print_help()
        return

    deep_dive(args.property, args.days, args.output)


if __name__ == "__main__":
    main()
