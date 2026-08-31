# SPEC — ga-deep-dive (Composio edition)

A parameterized skill: `deep-dive <property>` pulls **everything** GA4 (+GSC) offers for
that property and prints the full owner's-war-room report. Oracle target:
`docs/oracle/GOLDEN-TARGET.md`.

## Goals

- **One command, any property.** `deep-dive <name>` — no per-property code.
- **Single auth by default (Composio OAuth, no service-account key).** Native
  `google-analytics-data` OAuth kept as an optional second backend behind the same
  interface (`--backend native`), never a hard dependency.
- **Reproduce the full v3+v4 report** (see GOLDEN-TARGET.md) exactly, structurally.

## Non-goals (v1)

- No web UI. No new GA4 config writes (read-only reporting slugs only).
- No metered API keys anywhere (golden rule).

## Architecture (API-first, testable)

```
gadeepdive/
  registry.py     # property name -> {ga4_property_id, gsc_site?} ; loaded from config
  backends/
    base.py       # Backend protocol: run_report(dims,mets,**opts), run_realtime(...),
                  #   run_cohort(...), gsc_query(...)  -> normalized dict rows
    composio.py   # default; wraps GOOGLE_ANALYTICS_* + GSC slugs
    native.py     # optional; google-analytics-data SDK (behind --backend native)
  fetch.py        # section fetchers: each returns a plain dataclass/dict (NO formatting)
  health.py       # 7 health-score calculators (pure functions on fetched data)
  report.py       # renders sections -> ANSI / --json / --telegram (pure: data in, str out)
  cli.py          # arg parse, wire registry->backend->fetch->health->report
```

**Testability contract (enables TDD without live API):**
- `Backend` is an interface; tests inject a `FakeBackend` returning fixture rows.
- `fetch`, `health`, `report` are pure over backend output — unit-tested against fixtures.
- One live smoke test (opt-in, `GADD_LIVE=1`) hits Composio for esp-atlas to catch drift.

## CLI

`deep-dive <property> [--days N=7] [--json] [--no-gsc] [--no-telegram] [--backend composio|native]`

- **Defaults are all-in; params only subtract** (Felipe, 2026-08-31).
- Unknown property → clear error listing registered names.
- GSC section **included by default**; `--no-gsc` drops it.
- Telegram-safe condensed variant **produced by default** alongside the full ANSI; `--no-telegram` skips it.
- `--json` → structured dict of every section (same data, no art).

## Property registry (initial)

| name | ga4 property | gsc site |
|------|--------------|----------|
| esp-atlas | 551132215 | sc-domain:esp-atlas.com |
| abecmed | 291040306 | — |
| solvr | 523300499 | — |
| sonus | 517562144 | — |

Registry is data (config file), not code — adding a property is a config edit.

## Constraints (golden rules)

- TDD, ≥80% coverage. Each module ≤ ~900 lines (the old `deep_dive_v3.py` was 1,178 — split).
- Composio: batch dimension/metric pulls where possible (`BATCH_RUN_REPORTS`) to respect the
  10-metric / 9-dimension / 600-rpm limits noted in `TODO.md`.
- Every fetched section degrades gracefully to an explicit "no data" line, never a crash.

## Build order (oracle loop rounds)

1. **R1 — backend + skeleton + PART 1 §1–4** (banner, live-now, exec summary w/ WoW, health
   dashboard). FakeBackend fixtures + tests. Live smoke on esp-atlas.
2. **R2 — PART 1 §5–12** (acquisition, geo, content, segments, events, time, tech, insights).
3. **R3 — PART 2 §13–19** (scroll, flow, audiences, hourly, acq-over-time, mobile, close) + GSC.
4. **R4 — format polish** diffed against `docs/oracle/GOLDEN-TARGET.md` until structural match;
   wire `weekly` cron + optional email/telegram delivery.
