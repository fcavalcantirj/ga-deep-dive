#!/usr/bin/env python3
"""Cron entrypoint: run the Composio `deep-dive` report for a property and
deliver it to Telegram. All business logic lives in `gadeepdive.cli`; this
script only wires argv for unattended (cron) use.

Usage:
    python3 scripts/weekly_deepdive.py <property> [--days N]

Example crontab (Mondays at 9am):
    0 9 * * 1 cd /path/to/ga-deep-dive && .venv/bin/python3 scripts/weekly_deepdive.py esp-atlas
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gadeepdive import cli  # noqa: E402


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("Usage: weekly_deepdive.py <property> [--days N]", file=sys.stderr)
        return 1
    property_name, extra_args = argv[0], argv[1:]
    return cli.main([property_name, "--deliver", "telegram", *extra_args])


if __name__ == "__main__":
    sys.exit(main())
