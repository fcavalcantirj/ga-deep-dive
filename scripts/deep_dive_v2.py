#!/usr/bin/env python3
"""
GA4 DEEP DIVE v2 — OWNER'S DASHBOARD
Built for Solvr by Claudius 🏴‍☠️

What an owner needs to know:
1. Am I growing? (WoW, MoM comparisons)
2. Who's using my product? (user profiles)
3. What's working? (content performance)
4. What's broken? (drop-offs, bounces)
5. Where's traffic coming from? (acquisition)
6. Are users coming back? (retention)
7. What should I fix? (actionable insights)

Usage:
    python3 deep_dive_v2.py solvr
    python3 deep_dive_v2.py solvr --days 30
    python3 deep_dive_v2.py solvr --compare  # Compare with last snapshot
    python3 deep_dive_v2.py --list
"""

import argparse

from deep_dive_v2_analysis import (
    analyze_core_metrics, analyze_acquisition, analyze_content, analyze_users,
    analyze_geography, analyze_technology, analyze_time_patterns, analyze_events,
    calculate_health_scores
)
from deep_dive_v2_client import GA4Client
from deep_dive_v2_config import PROPERTIES
from deep_dive_v2_report import print_report, save_snapshot

# ============================================================================
# MAIN
# ============================================================================

def deep_dive(property_name: str, days: int = 30, compare: bool = False):
    """Run complete deep dive analysis."""

    property_id = PROPERTIES.get(property_name.lower(), property_name)
    is_solvr = property_name.lower() == 'solvr'

    print(f"\n🔄 Analyzing {property_name} (property {property_id})...")

    ga = GA4Client(property_id)

    # Collect all data
    data = {
        'realtime': ga.realtime(),
        'core': analyze_core_metrics(ga, days),
        'acquisition': analyze_acquisition(ga, days),
        'content': analyze_content(ga, days, is_solvr=is_solvr),
        'users': analyze_users(ga, days),
        'geography': analyze_geography(ga, days),
        'technology': analyze_technology(ga, days),
        'time': analyze_time_patterns(ga, days),
        'events': analyze_events(ga, days),
    }

    # Calculate health scores
    data['scores'] = calculate_health_scores(data)

    # Print report
    print_report(data, property_name, days)

    # Save snapshot
    save_snapshot(data, property_name, days)

    return data


def list_properties():
    """List known properties."""
    print("\n📋 Known Properties:\n")
    for name, prop_id in PROPERTIES.items():
        print(f"   {name:<15} → {prop_id}")
    print("\n   Usage: python3 deep_dive_v2.py <name>")


def main():
    parser = argparse.ArgumentParser(description='GA4 Deep Dive v2 — Owner Dashboard')
    parser.add_argument('property', nargs='?', help='Property name or ID')
    parser.add_argument('--days', type=int, default=30, help='Analysis period (default: 30)')
    parser.add_argument('--compare', action='store_true', help='Compare with last snapshot')
    parser.add_argument('--list', action='store_true', help='List known properties')

    args = parser.parse_args()

    if args.list:
        list_properties()
        return

    if not args.property:
        parser.print_help()
        return

    deep_dive(args.property, args.days, args.compare)


if __name__ == '__main__':
    main()
