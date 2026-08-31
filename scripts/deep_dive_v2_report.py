"""
GA4 DEEP DIVE v2 — OUTPUT FORMATTING
Console report rendering and snapshot persistence for the v2 CLI.
"""

import json
from datetime import datetime
from typing import Dict

from deep_dive_v2_analysis import Snapshot
from deep_dive_v2_config import PROPERTIES, SNAPSHOTS_DIR
from deep_dive_v2_utils import safe_int, safe_float, pct, dur, delta, score_bar, section, subsection

# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def print_report(data: Dict, property_name: str, days: int):
    """Print the full report."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔍 GA4 DEEP DIVE v2 — OWNER'S DASHBOARD                                     ║
║  Property: {property_name.upper():<20}  Period: Last {days} days                      ║
║  Generated: {now:<62}║
╚══════════════════════════════════════════════════════════════════════════════╝""")

    # ===== REALTIME =====
    section("🟢 RIGHT NOW")
    print(f"   Active Users: {data.get('realtime', 0)}")

    # ===== EXECUTIVE SUMMARY =====
    section("📊 EXECUTIVE SUMMARY")

    core = data.get('core', {})
    current = core.get('current', {})
    previous = core.get('previous', {})

    curr_sessions = safe_int(current.get('sessions', 0))
    prev_sessions = safe_int(previous.get('sessions', 0))
    curr_users = safe_int(current.get('totalUsers', 0))
    prev_users = safe_int(previous.get('totalUsers', 0))
    curr_eng = safe_float(current.get('engagementRate', 0))
    prev_eng = safe_float(previous.get('engagementRate', 0))

    print(f"""
   ┌─────────────────────┬──────────────┬──────────────┬────────────┐
   │ Metric              │ This Period  │ Last Period  │ Change     │
   ├─────────────────────┼──────────────┼──────────────┼────────────┤
   │ Sessions            │ {curr_sessions:>12,} │ {prev_sessions:>12,} │ {delta(curr_sessions, prev_sessions):>10} │
   │ Users               │ {curr_users:>12,} │ {prev_users:>12,} │ {delta(curr_users, prev_users):>10} │
   │ New Users           │ {safe_int(current.get('newUsers', 0)):>12,} │ {safe_int(previous.get('newUsers', 0)):>12,} │ {delta(safe_int(current.get('newUsers', 0)), safe_int(previous.get('newUsers', 0))):>10} │
   │ Engagement Rate     │ {pct(curr_eng):>12} │ {pct(prev_eng):>12} │ {delta(curr_eng, prev_eng):>10} │
   │ Bounce Rate         │ {pct(current.get('bounceRate', 0)):>12} │ {pct(previous.get('bounceRate', 0)):>12} │ — │
   │ Avg Duration        │ {dur(current.get('averageSessionDuration', 0)):>12} │ {dur(previous.get('averageSessionDuration', 0)):>12} │ — │
   │ Pages/Session       │ {safe_float(current.get('screenPageViewsPerSession', 0)):>12.2f} │ — │ — │
   │ Page Views          │ {safe_int(current.get('screenPageViews', 0)):>12,} │ {safe_int(previous.get('screenPageViews', 0)):>12,} │ {delta(safe_int(current.get('screenPageViews', 0)), safe_int(previous.get('screenPageViews', 0))):>10} │
   └─────────────────────┴──────────────┴──────────────┴────────────┘
""")

    # ===== HEALTH SCORES =====
    section("🏥 HEALTH SCORES")

    scores = data.get('scores', {})

    def grade(s):
        if s >= 80: return '✅'
        elif s >= 60: return '⚠️'
        else: return '❌'

    for name, score in scores.items():
        label = name.replace('_', ' ').title()
        print(f"   {grade(score)} {label:<20} {score_bar(score)} {score}/100")

    overall = int(sum(scores.values()) / len(scores)) if scores else 0
    letter = 'A' if overall >= 80 else 'B' if overall >= 65 else 'C' if overall >= 50 else 'D'
    print(f"\n   🎯 OVERALL: {overall}/100 (Grade {letter})")

    # ===== ACQUISITION =====
    section("🚦 WHERE USERS COME FROM")

    acq = data.get('acquisition', {})
    channels = acq.get('channels', [])

    if channels:
        total_sessions = sum(safe_int(c.get('sessions', 0)) for c in channels if '_error' not in c)
        print(f"\n   Channel Breakdown (total: {total_sessions:,} sessions)\n")
        print(f"   {'Channel':<20} {'Sessions':>8} {'Share':>8} {'Users':>7} {'Eng%':>7} {'Bnc%':>7}")
        print("   " + "─"*65)
        for c in channels[:10]:
            if '_error' in c: continue
            sess = safe_int(c.get('sessions', 0))
            share = sess / total_sessions * 100 if total_sessions > 0 else 0
            print(f"   {c.get('sessionDefaultChannelGroup', '?')[:19]:<20} {sess:>8,} {share:>7.1f}% {safe_int(c.get('totalUsers', 0)):>7,} {pct(c.get('engagementRate', 0)):>7} {pct(c.get('bounceRate', 0)):>7}")

    subsection("Top Referrers")
    referrers = acq.get('referrers', [])
    for r in referrers[:10]:
        if '_error' in r: continue
        ref = r.get('pageReferrer', '')[:50]
        if ref and ref != '(not set)':
            print(f"   {r.get('sessionSource', '?')[:15]:<16} {ref:<50} {safe_int(r.get('sessions', 0)):>5}")

    # ===== CONTENT PERFORMANCE =====
    section("📄 CONTENT PERFORMANCE")

    content = data.get('content', {})

    # Solvr content groups
    groups = content.get('content_groups', {})
    if groups:
        subsection("Content Groups (Solvr-specific)")
        print(f"   {'Group':<15} {'Pages':>6} {'Views':>8} {'Users':>7} {'Avg Eng':>8}")
        print("   " + "─"*50)
        for name, stats in sorted(groups.items(), key=lambda x: x[1].get('views', 0), reverse=True):
            if isinstance(stats, dict):
                print(f"   {name:<15} {stats.get('pages', 0):>6} {stats.get('views', 0):>8,} {stats.get('users', 0):>7,} {stats.get('avg_engagement', 0)*100:>7.1f}%")

    subsection("Top Pages")
    pages = content.get('pages', [])
    print(f"   {'Path':<40} {'Views':>7} {'Users':>6} {'Eng%':>6}")
    print("   " + "─"*65)
    for p in pages[:15]:
        if not p or '_error' in p: continue
        path = p.get('pagePath', '?')
        views = safe_int(p.get('screenPageViews', 0))
        users = safe_int(p.get('totalUsers', 0))
        eng = safe_float(p.get('engagementRate', 0))
        print(f"   {path[:39]:<40} {views:>7,} {users:>6,} {eng*100:>5.1f}%")

    subsection("🚨 Problem Pages (High Bounce)")
    high_bounce = content.get('high_bounce', [])
    if high_bounce:
        print(f"   {'Path':<45} {'Views':>7} {'Bounce':>8}")
        print("   " + "─"*65)
        for p in high_bounce[:8]:
            print(f"   {p.get('pagePath', '?')[:44]:<45} {safe_int(p.get('screenPageViews', 0)):>7,} {pct(p.get('bounceRate', 0)):>8}")
    else:
        print("   ✅ No high-bounce pages detected!")

    # ===== USER BEHAVIOR =====
    section("👤 USER BEHAVIOR")

    users = data.get('users', {})
    activity = users.get('activity', {})

    dau = safe_int(activity.get('active1DayUsers', 0))
    wau = safe_int(activity.get('active7DayUsers', 0))
    mau = safe_int(activity.get('active28DayUsers', 0))

    print(f"""
   Daily Active Users (DAU):   {dau:>8,}
   Weekly Active Users (WAU):  {wau:>8,}
   Monthly Active Users (MAU): {mau:>8,}

   DAU/WAU Stickiness: {dau/wau*100 if wau else 0:>6.1f}%  (how often users return weekly)
   DAU/MAU Stickiness: {dau/mau*100 if mau else 0:>6.1f}%  (how often users return monthly)
""")

    subsection("New vs Returning")
    nvr = users.get('new_vs_returning', [])
    for r in nvr:
        if '_error' in r: continue
        print(f"   {r.get('newVsReturning', '?'):<12}: {safe_int(r.get('sessions', 0)):>6} sessions, {pct(r.get('engagementRate', 0))} engaged, {pct(r.get('bounceRate', 0))} bounce")

    # ===== GEOGRAPHY =====
    section("🌍 GEOGRAPHY")

    geo = data.get('geography', {})
    countries = geo.get('countries', [])

    if countries:
        total = sum(safe_int(c.get('sessions', 0)) for c in countries if '_error' not in c)
        print(f"   {'Country':<20} {'Sessions':>8} {'Share':>7} {'Users':>7} {'Eng%':>7}")
        print("   " + "─"*55)
        for c in countries[:12]:
            if '_error' in c: continue
            sess = safe_int(c.get('sessions', 0))
            share = sess / total * 100 if total > 0 else 0
            print(f"   {c.get('country', '?')[:19]:<20} {sess:>8,} {share:>6.1f}% {safe_int(c.get('totalUsers', 0)):>7,} {pct(c.get('engagementRate', 0)):>7}")

    # ===== TECHNOLOGY =====
    section("💻 TECHNOLOGY")

    tech = data.get('technology', {})

    subsection("Devices")
    devices = tech.get('devices', [])
    total_dev = sum(safe_int(d.get('sessions', 0)) for d in devices if '_error' not in d)
    for d in devices:
        if '_error' in d: continue
        sess = safe_int(d.get('sessions', 0))
        share = sess / total_dev * 100 if total_dev > 0 else 0
        bar = '█' * int(share / 5)
        print(f"   {d.get('deviceCategory', '?'):<10} {bar:<20} {share:>5.1f}% ({sess:,})")

    subsection("Top Browsers")
    browsers = tech.get('browsers', [])
    for b in browsers[:6]:
        if '_error' in b: continue
        print(f"   {b.get('browser', '?')[:15]:<16} {safe_int(b.get('sessions', 0)):>6,} sessions, {pct(b.get('engagementRate', 0))} engaged")

    # ===== TIME PATTERNS =====
    section("🕐 TIME PATTERNS")

    time = data.get('time', {})

    subsection("Hour of Day (UTC)")
    hourly = time.get('hourly', [])
    if hourly:
        max_s = max(safe_int(h.get('sessions', 0)) for h in hourly)
        for h in hourly:
            sess = safe_int(h.get('sessions', 0))
            bar = '█' * int(sess / max_s * 15) if max_s > 0 else ''
            print(f"   {int(h.get('hour', 0)):02d}:00  {bar:<15} {sess:>5}")

    subsection("Day of Week")
    daily = time.get('daily', [])
    days_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    for d in daily:
        if '_error' in d: continue
        day_idx = int(d.get('dayOfWeek', 0))
        print(f"   {days_names[day_idx]:<4} {safe_int(d.get('sessions', 0)):>6} sessions, {pct(d.get('engagementRate', 0))} engaged")

    # ===== EVENTS =====
    section("⚡ EVENTS")

    events_data = data.get('events', {})
    events = events_data.get('events', [])

    print(f"   {'Event':<30} {'Count':>10} {'Users':>8} {'Per User':>10}")
    print("   " + "─"*65)
    for e in events[:12]:
        if '_error' in e: continue
        print(f"   {e.get('eventName', '?')[:29]:<30} {safe_int(e.get('eventCount', 0)):>10,} {safe_int(e.get('totalUsers', 0)):>8,} {safe_float(e.get('eventCountPerUser', 0)):>10.2f}")

    # ===== DAILY TREND =====
    section("📈 TREND (Last 14 Days)")

    trend = time.get('trend', [])[-14:]
    if trend:
        max_s = max(safe_int(t.get('sessions', 0)) for t in trend)
        for t in trend:
            sess = safe_int(t.get('sessions', 0))
            bar = '█' * int(sess / max_s * 20) if max_s > 0 else ''
            date = t.get('date', '')
            date_fmt = f"{date[4:6]}/{date[6:]}" if len(date) == 8 else date
            print(f"   {date_fmt}  {bar:<20} {sess:>5} ({safe_int(t.get('totalUsers', 0))} users)")

    # ===== RECOMMENDATIONS =====
    section("💡 ACTIONABLE INSIGHTS")

    insights = []

    # Traffic diversity
    if scores.get('traffic_diversity', 100) < 50 and channels:
        top = channels[0]
        pct_top = safe_int(top.get('sessions', 0)) / total_sessions * 100 if total_sessions > 0 else 0
        insights.append(f"⚠️  {pct_top:.0f}% of traffic from {top.get('sessionDefaultChannelGroup')} — diversify sources")

    # High bounce pages
    if high_bounce:
        worst = high_bounce[0]
        insights.append(f"🚨 Fix {worst.get('pagePath')} — {pct(worst.get('bounceRate'))} bounce rate")

    # Mobile
    if scores.get('mobile', 100) < 50:
        insights.append("📱 Low mobile traffic — check mobile UX")

    # Engagement
    if scores.get('engagement', 100) < 50:
        insights.append("📉 Low engagement — improve content or page speed")

    # Growth
    if scores.get('growth', 50) < 40:
        insights.append("📉 Traffic declining — investigate cause")
    elif scores.get('growth', 50) > 70:
        insights.append("📈 Strong growth! Keep doing what's working")

    # Retention
    if scores.get('retention', 50) < 30:
        insights.append("👋 Low retention — users aren't coming back")

    # No campaigns
    sources = acq.get('sources', [])
    has_campaigns = any(s.get('sessionMedium') in ['cpc', 'email', 'social'] for s in sources if '_error' not in s)
    if not has_campaigns:
        insights.append("📢 No tracked campaigns — consider UTM parameters")

    if insights:
        for insight in insights:
            print(f"   {insight}")
    else:
        print("   ✅ Looking good! No major issues detected.")

    print(f"\n{'='*80}")
    print("  ✅ DEEP DIVE COMPLETE")
    print(f"{'='*80}\n")


def save_snapshot(data: Dict, property_name: str, days: int):
    """Save snapshot for historical comparison."""

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    core = data.get('core', {}).get('current', {})
    activity = data.get('users', {}).get('activity', {})

    snapshot = Snapshot(
        property_id=PROPERTIES.get(property_name, property_name),
        property_name=property_name,
        generated_at=datetime.now().isoformat(),
        period_days=days,
        sessions=safe_int(core.get('sessions', 0)),
        users=safe_int(core.get('totalUsers', 0)),
        new_users=safe_int(core.get('newUsers', 0)),
        engagement_rate=safe_float(core.get('engagementRate', 0)),
        bounce_rate=safe_float(core.get('bounceRate', 0)),
        avg_duration=safe_float(core.get('averageSessionDuration', 0)),
        pages_per_session=safe_float(core.get('screenPageViewsPerSession', 0)),
        page_views=safe_int(core.get('screenPageViews', 0)),
        events=safe_int(core.get('eventCount', 0)),
        dau=safe_int(activity.get('active1DayUsers', 0)),
        wau=safe_int(activity.get('active7DayUsers', 0)),
        mau=safe_int(activity.get('active28DayUsers', 0)),
        top_channels=data.get('acquisition', {}).get('channels', [])[:5],
        top_pages=data.get('content', {}).get('pages', [])[:10],
        top_countries=data.get('geography', {}).get('countries', [])[:5],
        content_groups=data.get('content', {}).get('content_groups'),
        scores=data.get('scores'),
        overall_score=int(sum(data.get('scores', {}).values()) / len(data.get('scores', {}))) if data.get('scores') else 0
    )

    # Save with date
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{property_name}_{date_str}.json"
    filepath = SNAPSHOTS_DIR / filename

    with open(filepath, 'w') as f:
        json.dump(snapshot.to_dict(), f, indent=2, default=str)

    print(f"   💾 Snapshot saved: {filepath}")
