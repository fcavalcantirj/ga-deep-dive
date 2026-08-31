"""`deep-dive <property>` — argparse wiring: registry -> backend -> fetch ->
health -> report.

Defaults are all-in; flags only subtract (Felipe, 2026-08-31): GSC and the
telegram variant are produced unless explicitly suppressed.
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import charts, delivery, fetch, fetch_activity, fetch_content, fetch_gsc, fetch_part2, fetch_segments, fetch_technology, fetch_traffic, health, insights, registry, report
from .backends.composio import ComposioBackend
from .backends.native import NativeBackend

BACKEND_FACTORIES = {
    "composio": lambda prop: ComposioBackend(ga4_property_id=prop["ga4_property_id"], gsc_site=prop["gsc_site"]),
    "native": lambda prop: NativeBackend(ga4_property_id=prop["ga4_property_id"], gsc_site=prop["gsc_site"]),
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deep-dive", description="GA4 Deep Dive — the owner's war room, any property.")
    parser.add_argument("property", help="Registered property name (see config/properties.json)")
    parser.add_argument("--days", type=int, default=7, help="Period length in days (default: 7)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of the ANSI report")
    parser.add_argument("--no-gsc", action="store_true", help="Skip the Google Search Console section")
    parser.add_argument("--no-telegram", action="store_true", help="Skip the telegram-condensed variant")
    parser.add_argument("--backend", choices=sorted(BACKEND_FACTORIES), default="composio", help="Data backend (default: composio)")
    parser.add_argument(
        "--deliver", choices=sorted(delivery.DELIVERY_SENDERS), default=None, help="Render the dashboard and deliver it as a photo to a channel"
    )
    parser.add_argument("--dashboard", metavar="PATH", default=None, help="Write the visual dashboard PNG to PATH without delivering it")
    return parser


def _make_backend(backend_name: str, prop: Dict[str, Optional[str]]):
    return BACKEND_FACTORIES[backend_name](prop)


def _utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def collect_report_data(backend, property_name: str, days: int, no_gsc: bool = False) -> Dict[str, Any]:
    realtime = fetch.realtime_active_users(backend)
    executive = fetch.executive_summary(backend, days)
    activity = fetch.user_activity(backend)
    acquisition = fetch_traffic.acquisition(backend, days)
    geography = fetch_traffic.geography(backend, days)
    content = fetch_content.content(backend, days)
    segments = fetch_segments.user_segments(backend, days)
    events = fetch_activity.events(backend, days)
    time_patterns = fetch_activity.time_patterns(backend, days)
    technology = fetch_technology.technology(backend, days)
    dashboard = health.compute_dashboard(executive, activity, acquisition, geography, content, segments)

    scroll_depth = fetch_part2.scroll_depth(backend, days)
    user_flow = fetch_part2.user_flow(backend, days)
    audiences = fetch_part2.audiences(backend, days)
    hourly_performance = fetch_part2.hourly_performance(backend, days)
    acquisition_over_time = fetch_part2.acquisition_over_time(backend, days)
    mobile_devices = fetch_part2.mobile_devices(backend, days)
    gsc = None if no_gsc else fetch_gsc.gsc_report(backend, days)

    data = {
        "property": property_name,
        "days": days,
        "generated_at": _utc_now_str(),
        "realtime": realtime,
        "executive": executive,
        "activity": activity,
        "health": dashboard,
        "acquisition": acquisition,
        "geography": geography,
        "content": content,
        "segments": segments,
        "events": events,
        "time_patterns": time_patterns,
        "technology": technology,
        "scroll_depth": scroll_depth,
        "user_flow": user_flow,
        "audiences": audiences,
        "hourly_performance": hourly_performance,
        "acquisition_over_time": acquisition_over_time,
        "mobile_devices": mobile_devices,
        "gsc": gsc,
    }
    data["insights"] = insights.compute(data)
    return data


def _deliver_dashboard(data: Dict[str, Any], property_name: str, days: int) -> None:
    """Render the visual dashboard to a temp PNG and send it to Telegram as a
    photo with a concise caption — replaces the old text-wall delivery."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        image_path = charts.compose_dashboard(data, property_name, days, os.path.join(tmp_dir, "dashboard.png"))
        caption = charts.compose_caption(data, property_name, days)
        delivery.send_photo(image_path, caption)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        prop = registry.get_property(args.property)
    except registry.UnknownPropertyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    backend = _make_backend(args.backend, prop)
    data = collect_report_data(backend, args.property, args.days, no_gsc=args.no_gsc)
    data["goal"] = prop.get("goal")

    if args.dashboard:
        charts.compose_dashboard(data, args.property, args.days, args.dashboard)
        print(f"Dashboard written to {args.dashboard}.", file=sys.stderr)

    if args.deliver:
        try:
            _deliver_dashboard(data, args.property, args.days)
        except delivery.DeliveryError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Delivered to {args.deliver}.", file=sys.stderr)

    if args.json:
        print(json.dumps(report.render(data, "json"), indent=2))
        return 0

    print(report.render(data, "full"))
    if not args.no_telegram:
        print()
        print("=" * 40)
        print("TELEGRAM VARIANT")
        print("=" * 40)
        print(report.render(data, "telegram"))

    return 0


def run() -> None:
    sys.exit(main())


if __name__ == "__main__":
    run()
