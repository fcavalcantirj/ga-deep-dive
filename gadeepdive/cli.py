"""`deep-dive <property>` — argparse wiring: registry -> backend -> fetch ->
health -> report.

Defaults are all-in; flags only subtract (Felipe, 2026-08-31): GSC and the
telegram variant are produced unless explicitly suppressed.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import fetch, health, registry, report
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
    return parser


def _make_backend(backend_name: str, prop: Dict[str, Optional[str]]):
    return BACKEND_FACTORIES[backend_name](prop)


def _utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def collect_report_data(backend, property_name: str, days: int) -> Dict[str, Any]:
    realtime = fetch.realtime_active_users(backend)
    executive = fetch.executive_summary(backend, days)
    activity = fetch.user_activity(backend)
    dashboard = health.compute_dashboard(executive, activity)

    return {
        "property": property_name,
        "days": days,
        "generated_at": _utc_now_str(),
        "realtime": realtime,
        "executive": executive,
        "activity": activity,
        "health": dashboard,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        prop = registry.get_property(args.property)
    except registry.UnknownPropertyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    backend = _make_backend(args.backend, prop)
    data = collect_report_data(backend, args.property, args.days)

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
