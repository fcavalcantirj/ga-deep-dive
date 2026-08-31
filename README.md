# GA4 Deep Dive 🏴‍☠️

Comprehensive Google Analytics 4 property analysis — extracts EVERYTHING the API offers.

Built by Claudius for Solvr.

## `deep-dive` — the Composio-backed command (recommended)

The current, actively-maintained way to run a report. Auth is Composio OAuth by
default — **no service-account key required**. The legacy `deep_dive_v3.py` /
`deep_dive_v4.py` scripts below still work as a fallback (`--backend native`
uses the same `google-analytics-data` OAuth flow they used) but are no longer
where new work lands.

```bash
pip install -e .   # registers the `deep-dive` console script (see pyproject.toml)

deep-dive <property> [--days N] [--json] [--no-gsc] [--no-telegram] \
                      [--deliver telegram] [--dashboard PATH] [--backend composio|native]
```

| Flag | Default | Effect |
|------|---------|--------|
| `--days N` | 7 | Report period length |
| `--json` | off | Machine-readable output, no ANSI art |
| `--no-gsc` | off | Skip the Search Console section (included by default) |
| `--no-telegram` | off | Skip the telegram-condensed variant printed after the full report |
| `--dashboard PATH` | off | Render the visual dashboard PNG to `PATH` without sending it anywhere |
| `--deliver telegram` | off | Render the visual dashboard and send it to Telegram as a photo, with a short caption (needs `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`/`TELEGRAM_HOME_CHANNEL` env vars) |
| `--backend composio\|native` | `composio` | Data source — Composio OAuth (default, no key file) or the native SDK |

`--deliver telegram` sends a single dark-themed portrait dashboard image (KPI
tiles, health scores, acquisition, geography, hourly performance, event
funnel, GSC striking distance, ...) built by `gadeepdive/charts.py` — the old
wall-of-text "TELEGRAM VARIANT" is no longer what gets delivered to mobile.

**Defaults are all-in; flags only subtract.** GSC and the telegram variant ship
unless explicitly suppressed.

### Property registry

`<property>` resolves via `config/properties.json` (name → `{ga4_property_id,
gsc_site}`). Adding a property is a config edit, not a code change:

| name | ga4 property | gsc site |
|------|--------------|----------|
| esp-atlas | 551132215 | sc-domain:esp-atlas.com |
| abecmed | 291040306 | — |
| solvr | 523300499 | — |
| sonus | 517562144 | — |

### Weekly cron delivery

`scripts/weekly_deepdive.py` is a thin cron entrypoint that runs `deep-dive`
for one property and delivers it to Telegram:

```bash
0 9 * * 1 cd /path/to/ga-deep-dive && .venv/bin/python3 scripts/weekly_deepdive.py esp-atlas
```

See `SPEC.md` and `docs/oracle/GOLDEN-TARGET.md` for the full architecture and
report structure contract.

## Legacy scripts (deep_dive_v3 / v4)

## Features

### Scripts

| Script | Purpose |
|--------|---------|
| `deep_dive_v3.py` | Executive summary with health scores |
| `deep_dive_v4.py` | THE FULL MONTY — everything GA4 can tell you |
| `send_report_email.py` | Email reports via AgentMail |
| `weekly_report.py` | Weekly comparison reports |

### V3 — Executive Summary
- Period comparison (this vs last)
- Health scores (7 dimensions)
- Traffic source analysis
- Content performance
- User segments
- Time patterns

### V4 — The Full Monty
- Scroll depth analysis
- Outbound link tracking
- Site search analysis
- Demographics (with Google Signals)
- Search Console integration
- Cohort retention
- Custom audience performance
- Event deep dive
- Mobile device breakdown

## Setup

```bash
cd ~/development/ga-deep-dive
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Auth (first time)

1. Create OAuth credentials in Google Cloud Console
2. Place `credentials.json` at `~/.config/ga-deep-dive/credentials.json`
3. Run any script — it will prompt for auth

## Usage

```bash
# Quick executive summary
python3 scripts/deep_dive_v3.py solvr

# Full analysis
python3 scripts/deep_dive_v4.py solvr --days 30

# Email report
python3 scripts/send_report_email.py
```

## Cron Setup

Bi-weekly reports (Mon & Thu at 9am São Paulo):
```bash
0 12 * * 1,4 cd ~/development/ga-deep-dive && .venv/bin/python3 scripts/send_report_email.py >> data/cron.log 2>&1
```

## Properties

| Name | Property ID |
|------|-------------|
| solvr | 523300499 |
| abecmed | 291040306 |
| sonus | 517562144 |

---
*Built for owners who want to UNDERSTAND their product, not just see numbers.* 🏴‍☠️
