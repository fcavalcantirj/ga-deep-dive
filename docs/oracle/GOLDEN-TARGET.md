# Oracle golden target — `deep-dive <property>` full report

This is the **structural contract** the report must reproduce, annotated from the
reference SOLVR run (2026-03-03). The oracle loop iterates the implementation until a
run's output matches this structure section-for-section.

## What must match (structure) vs. what varies (data)

- **MUST MATCH (oracle-checked):** section presence, section order, section headers/emoji,
  column sets per table, the visual elements (health bars `█░`, quality stars `★`, sparkline
  bars, `← PEAK` / `← BEST` markers), the banner, PART 1 / PART 2 split, and the closing block.
- **VARIES (never oracle-checked):** every number, property name, date, country/page/device
  list contents, and the specific insights fired. A property with no data for a section
  (e.g. demographics below Google Signals threshold) prints an explicit
  "no data" line — it does **not** drop the section header.

## Invocation contract

```
deep-dive <property> [--days N] [--json] [--telegram]
```
- `<property>` resolves via the property registry (name → GA4 property id).
- default `--days 7`; report title states the period.
- `--json` emits the same data machine-readable (skips ANSI art).
- `--telegram` emits a width-safe condensed variant (no box-art) for phone delivery.

## Ordered section checklist (the oracle)

### Banner
- `🏴‍☠️ <PROPERTY> FULL ANALYTICS REPORT`, `Generated: <UTC ts>`, `Period: Last N days`.

### PART 1 — EXECUTIVE SUMMARY (v3)
1. **Banner box** — "GA4 DEEP DIVE v3 — THE OWNER'S WAR ROOM", property + period.
2. **🟢 LIVE NOW** — realtime active users (`RUN_REALTIME_REPORT`).
3. **📊 EXECUTIVE SUMMARY** — table: Metric | Current | Previous | Change, with 🟢/↓ arrows and
   `NEW` where no prior value. Rows: Sessions, Users, New Users, Engaged Sessions,
   Engagement Rate, Bounce Rate, Avg Duration (s), Pages/Session, Page Views.
   Then **📈 User Activity**: DAU / WAU / MAU + Stickiness (DAU/WAU, DAU/MAU).
4. **🏥 HEALTH DASHBOARD** — 7 scores as `█░` bars + status icon (✅/⚠️/🔴), sorted best→worst:
   Growth, Content, Engagement, Mobile, Geo Diversity, Retention, Traffic Diversity.
   Then **🎯 OVERALL SCORE: N/100 (Grade …)**.
5. **🚦 ACQUISITION** — Channel | Sessions | Share | Engaged | Bounce | Dur; + Top Referrer;
   + **First-Touch Attribution** (source, medium, sessions, share).
6. **🌍 GEOGRAPHY** — Country | Sessions | Share | Engaged | Quality(★); + Languages.
7. **📄 CONTENT** — Section | Views | Users | Engagement | Pages; + **🔥 Trending Up** (%±);
   + **🚨 Problem Pages** (100% bounce etc.).
8. **👤 USER SEGMENTS** — new vs returning table; + By Device bars.
9. **⚡ EVENTS** — event | count | per-user rate.
10. **🕐 TIME PATTERNS** — Day-of-Week bars (+ engaged%); + Last-7-days sparkline w/ `← PEAK`.
11. **💻 TECHNOLOGY** — Browsers (sessions, engaged%); + Top Resolutions.
12. **💡 ACTIONABLE INSIGHTS** — 🔴/🚨/🟢 lines with `→` recommendations, data-driven.

### PART 2 — THE FULL MONTY (v4)
13. **📜 SCROLL DEPTH** — depth buckets + per-page completion rates.
14. **🚪 USER FLOW — ENTRY POINTS** — entry page | entries | bounce%.
15. **🎯 GA4 AUDIENCES** — audience | users | sessions | rate (explicit "no audiences" if none).
16. **🕐 HOURLY PERFORMANCE** — Hour | Sessions | Engaged | Eng Rate | Avg Dur, w/ `← BEST`.
17. **📅 ACQUISITION OVER TIME** — per-day user bars, sorted.
18. **📱 MOBILE DEVICES** — device model | sessions.
19. **✅ FULL MONTY COMPLETE** — closing block: property + period.

## Data-source map (all confirmed ✅ on Composio, 2026-08-31)

Composio slug `GOOGLE_ANALYTICS_RUN_REPORT` covers §3–18 via dimension/metric swaps;
`RUN_REALTIME_REPORT` for §2; `cohortSpec` param for retention; multi-`dateRanges` for the
Current/Previous comparison; `GOOGLE_SEARCH_CONSOLE_SEARCH_ANALYTICS_QUERY` for the GSC add-on.
Soft spot: `userAgeBracket`/`userGender` return 0 rows on properties without Google Signals →
print "no demographic data (enable Google Signals)".
