"""
GA4 DEEP DIVE v3 — OUTPUT
Console report rendering and snapshot persistence for the v3 CLI.
"""

import json
from datetime import datetime
from typing import Dict

from deep_dive_v3_config import PROPERTIES, SNAPSHOTS_DIR
from deep_dive_v3_utils import safe_int, safe_float, pct, fmt_num, delta_str, bar, sparkline, section, subsection

# ============================================================================
# OUTPUT
# ============================================================================

def print_report(data: Dict, property_name: str, days: int):
    """Print comprehensive report."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    print(f"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║   🏴‍☠️  GA4 DEEP DIVE v3 — THE OWNER'S WAR ROOM                                    ║
║                                                                                  ║
║   Property: {property_name.upper():<15}     Period: Last {days} days                          ║
║   Generated: {now:<63}║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
""")

    # ===== REAL-TIME =====
    rt = data.get("realtime", 0)
    print(f"   🟢 LIVE NOW: {rt} active user{'s' if rt != 1 else ''}")

    # ===== EXECUTIVE SUMMARY =====
    section("EXECUTIVE SUMMARY", "📊")

    exec_data = data.get("executive", {})
    curr = exec_data.get("current", {})
    prev = exec_data.get("previous", {})
    activity = exec_data.get("activity", {})

    # Key metrics table
    metrics = [
        ("Sessions", "sessions", False),
        ("Users", "totalUsers", False),
        ("New Users", "newUsers", False),
        ("Engaged Sessions", "engagedSessions", False),
        ("Engagement Rate", "engagementRate", False),
        ("Bounce Rate", "bounceRate", True),  # reverse=True (down is good)
        ("Avg Duration (s)", "averageSessionDuration", False),
        ("Pages/Session", "screenPageViewsPerSession", False),
        ("Page Views", "screenPageViews", False),
    ]

    print(f"\n   {'Metric':<22} {'Current':>12} {'Previous':>12} {'Change':>12}")
    print(f"   {'─'*60}")

    for label, key, reverse in metrics:
        c_val = safe_float(curr.get(key, 0))
        p_val = safe_float(prev.get(key, 0))

        if "Rate" in label:
            c_str = pct(c_val)
            p_str = pct(p_val) if p_val else "—"
        elif "Duration" in label:
            c_str = f"{c_val:.0f}s"
            p_str = f"{p_val:.0f}s" if p_val else "—"
        elif "Pages" in label and "Views" not in label:
            c_str = f"{c_val:.2f}"
            p_str = f"{p_val:.2f}" if p_val else "—"
        else:
            c_str = fmt_num(c_val)
            p_str = fmt_num(p_val) if p_val else "—"

        change = delta_str(c_val, p_val, reverse)
        print(f"   {label:<22} {c_str:>12} {p_str:>12} {change:>12}")

    # Activity metrics
    dau = safe_int(activity.get("active1DayUsers", 0))
    wau = safe_int(activity.get("active7DayUsers", 0))
    mau = safe_int(activity.get("active28DayUsers", 0))

    print(f"\n   📈 User Activity:")
    print(f"      DAU: {dau:,}  |  WAU: {wau:,}  |  MAU: {mau:,}")
    print(f"      Stickiness: DAU/WAU={dau/wau*100:.1f}%  DAU/MAU={dau/mau*100:.1f}%" if wau and mau else "")

    # ===== HEALTH SCORES =====
    section("HEALTH DASHBOARD", "🏥")

    scores = data.get("scores", {})

    def grade_emoji(s):
        if s >= 80: return "✅"
        elif s >= 60: return "⚠️"
        else: return "🔴"

    print()
    for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        label = name.replace("_", " ").title()
        print(f"   {grade_emoji(score)} {label:<20} {bar(score, 100, 25)} {score:>3}/100")

    overall = int(sum(scores.values()) / len(scores)) if scores else 0
    grade = "A+" if overall >= 90 else "A" if overall >= 80 else "B" if overall >= 65 else "C" if overall >= 50 else "D"
    print(f"\n   {'═'*50}")
    print(f"   🎯 OVERALL SCORE: {overall}/100 (Grade {grade})")

    # ===== ACQUISITION DEEP DIVE =====
    section("ACQUISITION — WHERE DO USERS COME FROM?", "🚦")

    acq = data.get("acquisition", {})
    channels = acq.get("channels", [])

    if channels:
        total = sum(safe_int(c.get("sessions", 0)) for c in channels if "_error" not in c)

        subsection("Channel Performance")
        print(f"\n   {'Channel':<18} {'Sessions':>8} {'Share':>7} {'Engaged':>8} {'Bounce':>8} {'Dur':>6}")
        print(f"   {'─'*65}")

        for c in channels[:8]:
            if "_error" in c: continue
            sess = safe_int(c.get("sessions", 0))
            share = sess / total * 100 if total else 0
            engaged = safe_int(c.get("engagedSessions", 0))
            eng_pct = engaged / sess * 100 if sess else 0
            bounce = safe_float(c.get("bounceRate", 0)) * 100
            dur = safe_float(c.get("averageSessionDuration", 0))

            print(f"   {c.get('sessionDefaultChannelGroup', '?')[:17]:<18} {sess:>8,} {share:>6.1f}% {eng_pct:>7.1f}% {bounce:>7.1f}% {dur:>5.0f}s")

    # Top referrers
    referrers = acq.get("referrers", [])
    if referrers:
        subsection("Top Referrers (actual URLs)")
        for r in referrers[:8]:
            if "_error" in r: continue
            url = r.get("pageReferrer", "")
            if url and url != "(not set)" and not url.startswith("https://solvr.dev"):
                print(f"   {url[:65]:<66} {safe_int(r.get('sessions', 0)):>5}")

    # First touch attribution
    first = acq.get("first_touch", [])
    if first:
        subsection("First-Touch Attribution (how users FOUND you)")
        print(f"\n   {'Source':<20} {'Medium':<12} {'Users':>8} {'Engaged':>8}")
        print(f"   {'─'*55}")
        for f in first[:8]:
            if "_error" in f: continue
            print(f"   {f.get('firstUserSource', '?')[:19]:<20} {f.get('firstUserMedium', '?')[:11]:<12} {safe_int(f.get('totalUsers', 0)):>8} {pct(f.get('engagementRate', 0)):>8}")

    # ===== GEOGRAPHY =====
    section("GEOGRAPHY — WHERE ARE YOUR USERS?", "🌍")

    geo = data.get("geography", {})
    countries = geo.get("countries", [])

    if countries:
        total = sum(safe_int(c.get("sessions", 0)) for c in countries if "_error" not in c)

        subsection("Country Performance (sorted by quality)")
        print(f"\n   {'Country':<20} {'Sessions':>8} {'Share':>7} {'Engaged':>8} {'Quality':>8}")
        print(f"   {'─'*60}")

        # Sort by quality score
        ranked = sorted([c for c in countries if "_error" not in c],
                       key=lambda x: x.get("quality_score", 0), reverse=True)

        for c in ranked[:12]:
            sess = safe_int(c.get("sessions", 0))
            share = sess / total * 100 if total else 0
            engaged = pct(c.get("engagementRate", 0))
            quality = c.get("quality_score", 0)
            quality_bar = "★" * min(int(quality / 2), 5)

            print(f"   {c.get('country', '?')[:19]:<20} {sess:>8,} {share:>6.1f}% {engaged:>8} {quality_bar:<8}")

    # Languages
    languages = geo.get("languages", [])
    if languages:
        subsection("Languages")
        lang_total = sum(safe_int(l.get("totalUsers", 0)) for l in languages if "_error" not in l)
        for l in languages[:8]:
            if "_error" in l: continue
            users = safe_int(l.get("totalUsers", 0))
            share = users / lang_total * 100 if lang_total else 0
            print(f"   {l.get('language', '?')[:25]:<26} {users:>6} users ({share:.1f}%)")

    # ===== CONTENT =====
    section("CONTENT — WHAT'S WORKING?", "📄")

    content = data.get("content", {})

    # Content groups (Solvr)
    groups = content.get("content_groups", {})
    if groups:
        subsection("Solvr Content Groups")
        print(f"\n   {'Section':<15} {'Views':>8} {'Users':>7} {'Engagement':>10} {'Pages':>6}")
        print(f"   {'─'*55}")

        for name, stats in sorted(groups.items(), key=lambda x: x[1].get("views", 0), reverse=True):
            print(f"   {name:<15} {stats.get('views', 0):>8,} {stats.get('users', 0):>7,} {stats.get('avg_engagement', 0)*100:>9.1f}% {stats.get('pages', 0):>6}")

    # Trending pages
    trending = content.get("trending", [])
    if trending:
        subsection("🔥 Trending Up (this week vs last)")
        for p in trending[:5]:
            if p.get("trend", 0) > 0:
                print(f"   {p.get('pagePath', '?')[:45]:<46} +{p.get('trend', 0):.0f}%")

    # Declining pages
    declining = content.get("declining", [])
    if declining:
        subsection("📉 Declining")
        for p in declining[:5]:
            if p.get("trend", 0) < 0:
                print(f"   {p.get('pagePath', '?')[:45]:<46} {p.get('trend', 0):.0f}%")

    # Problem pages
    high_bounce = content.get("high_bounce", [])
    if high_bounce:
        subsection("🚨 Problem Pages (high bounce)")
        print(f"\n   {'Page':<45} {'Views':>7} {'Bounce':>8}")
        print(f"   {'─'*65}")
        for p in high_bounce[:8]:
            print(f"   {p.get('pagePath', '?')[:44]:<45} {safe_int(p.get('screenPageViews', 0)):>7} {pct(p.get('bounceRate', 0)):>8}")

    # ===== USER SEGMENTS =====
    section("USER SEGMENTS — WHO ARE YOUR USERS?", "👤")

    segments = data.get("segments", {})

    # New vs returning
    nvr = segments.get("new_vs_returning", [])
    if nvr:
        subsection("New vs Returning")
        print(f"\n   {'Segment':<15} {'Sessions':>10} {'Users':>8} {'Engaged':>10} {'Quality':>8}")
        print(f"   {'─'*60}")

        for s in nvr:
            if "_error" in s: continue
            name = s.get("newVsReturning", "?")
            if not name: continue
            quality = s.get("quality", 0) * 100
            print(f"   {name:<15} {safe_int(s.get('sessions', 0)):>10,} {safe_int(s.get('totalUsers', 0)):>8,} {pct(s.get('engagementRate', 0)):>10} {quality:>7.0f}%")

    # By device
    devices = segments.get("by_device", [])
    if devices:
        subsection("By Device")
        total_dev = sum(safe_int(d.get("sessions", 0)) for d in devices if "_error" not in d)
        for d in devices:
            if "_error" in d: continue
            sess = safe_int(d.get("sessions", 0))
            share = sess / total_dev * 100 if total_dev else 0
            device_bar = bar(share, 100, 15)
            print(f"   {d.get('deviceCategory', '?'):<10} {device_bar} {share:>5.1f}% ({sess:,} sessions)")

    # ===== EVENTS =====
    section("EVENTS — WHAT DO USERS DO?", "⚡")

    events_data = data.get("events", {})
    events = events_data.get("events", [])

    if events:
        # Get total users from activity data (more reliable)
        total_users = safe_int(activity.get("active28DayUsers", 0)) or 1

        print(f"\n   {'Event':<30} {'Count':>10} {'Users':>8} {'% Users':>8} {'Per User':>10}")
        print(f"   {'─'*75}")

        for e in events[:15]:
            if "_error" in e: continue
            count = safe_int(e.get("eventCount", 0))
            users = safe_int(e.get("totalUsers", 0))
            user_pct = min(users / total_users * 100, 100) if total_users else 0
            per_user = safe_float(e.get("eventCountPerUser", 0))

            print(f"   {e.get('eventName', '?')[:29]:<30} {count:>10,} {users:>8,} {user_pct:>7.1f}% {per_user:>10.2f}")

    # Custom events highlight
    custom = events_data.get("custom_events", [])
    if custom:
        subsection("Custom Events (your tracking)")
        for e in custom[:5]:
            print(f"   {e.get('eventName', '?'):<30} {safe_int(e.get('eventCount', 0)):>10,} ({safe_int(e.get('totalUsers', 0))} users)")

    # ===== TIME PATTERNS =====
    section("TIME PATTERNS — WHEN DO USERS ENGAGE?", "🕐")

    time_data = data.get("time", {})

    # Hourly heatmap
    hourly = time_data.get("hourly", [])
    if hourly:
        subsection("Hour of Day (UTC)")
        max_sess = max(safe_int(h.get("sessions", 0)) for h in hourly) or 1

        # Morning, afternoon, evening, night
        print("\n   Morning (6-12):  ", end="")
        for h in hourly:
            hr = int(h.get("hour", 0))
            if 6 <= hr < 12:
                intensity = safe_int(h.get("sessions", 0)) / max_sess
                char = "░▒▓█"[min(int(intensity * 4), 3)]
                print(char, end="")

        print("\n   Afternoon (12-18):", end="")
        for h in hourly:
            hr = int(h.get("hour", 0))
            if 12 <= hr < 18:
                intensity = safe_int(h.get("sessions", 0)) / max_sess
                char = "░▒▓█"[min(int(intensity * 4), 3)]
                print(char, end="")

        print("\n   Evening (18-24): ", end="")
        for h in hourly:
            hr = int(h.get("hour", 0))
            if 18 <= hr < 24:
                intensity = safe_int(h.get("sessions", 0)) / max_sess
                char = "░▒▓█"[min(int(intensity * 4), 3)]
                print(char, end="")

        print("\n   Night (0-6):     ", end="")
        for h in hourly:
            hr = int(h.get("hour", 0))
            if 0 <= hr < 6:
                intensity = safe_int(h.get("sessions", 0)) / max_sess
                char = "░▒▓█"[min(int(intensity * 4), 3)]
                print(char, end="")
        print()

    # Day of week
    daily = time_data.get("daily", [])
    if daily:
        subsection("Day of Week")
        days_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        max_d = max(safe_int(d.get("sessions", 0)) for d in daily) or 1

        for d in daily:
            dow = int(d.get("dayOfWeek", 0))
            sess = safe_int(d.get("sessions", 0))
            day_bar = bar(sess, max_d, 15)
            print(f"   {days_names[dow]:<4} {day_bar} {sess:>5} sessions ({pct(d.get('engagementRate', 0))} engaged)")

    # Trend sparkline
    trend = time_data.get("trend", [])
    if trend:
        subsection(f"Daily Trend (last {len(trend)} days)")
        sessions = [safe_int(t.get("sessions", 0)) for t in trend]
        spark = sparkline(sessions)
        print(f"\n   {spark}")
        print(f"   Min: {min(sessions)}  Max: {max(sessions)}  Avg: {sum(sessions)//len(sessions)}")

        # Last 7 days detail
        print(f"\n   Last 7 days:")
        for t in trend[-7:]:
            date = t.get("date", "")
            date_fmt = f"{date[4:6]}/{date[6:]}" if len(date) == 8 else date
            sess = safe_int(t.get("sessions", 0))
            users = safe_int(t.get("totalUsers", 0))
            rolling = t.get("rolling_avg")
            rolling_str = f"(7d avg: {rolling:.0f})" if rolling else ""
            print(f"      {date_fmt}: {sess:>4} sessions, {users:>4} users {rolling_str}")

    # ===== TECHNOLOGY =====
    section("TECHNOLOGY", "💻")

    tech = data.get("technology", {})

    # Browsers
    browsers = tech.get("browsers", [])
    if browsers:
        subsection("Browsers")
        for b in browsers[:8]:
            if "_error" in b: continue
            sess = safe_int(b.get("sessions", 0))
            eng = pct(b.get("engagementRate", 0))
            bounce = pct(b.get("bounceRate", 0))
            print(f"   {b.get('browser', '?')[:15]:<16} {sess:>6} sessions | {eng} engaged | {bounce} bounce")

    # Screen resolutions
    screens = tech.get("screens", [])
    if screens:
        subsection("Screen Resolutions (design targets)")
        for s in screens[:8]:
            if "_error" in s: continue
            print(f"   {s.get('screenResolution', '?'):<15} {safe_int(s.get('sessions', 0)):>6} sessions")

    # ===== ACTIONABLE INSIGHTS =====
    section("ACTIONABLE INSIGHTS — WHAT TO DO NEXT", "💡")

    insights = []

    # Traffic diversity
    if scores.get("traffic_diversity", 100) < 50 and channels:
        top = channels[0]
        top_pct = safe_int(top.get("sessions", 0)) / total * 100 if total else 0
        insights.append(f"🔴 {top_pct:.0f}% traffic from {top.get('sessionDefaultChannelGroup')} — DIVERSIFY NOW")
        insights.append(f"   → Try: SEO content, social posting, email newsletter, partnerships")

    # Retention
    if scores.get("retention", 100) < 50:
        dau_mau_pct = dau / mau * 100 if mau > 0 else 0
        insights.append(f"🔴 Low retention (DAU/MAU={dau_mau_pct:.1f}%) — users aren't returning")
        insights.append(f"   → Try: Email re-engagement, push notifications, feature announcements")

    # High bounce pages
    if high_bounce:
        worst = high_bounce[0]
        insights.append(f"🚨 Fix {worst.get('pagePath')} — {pct(worst.get('bounceRate'))} bounce rate")
        insights.append(f"   → Check: page load speed, content relevance, mobile experience")

    # Growth
    if scores.get("growth", 50) > 70:
        insights.append(f"🟢 Strong growth! Double down on what's working")
    elif scores.get("growth", 50) < 40:
        insights.append(f"🔴 Traffic declining — investigate cause ASAP")

    # Mobile
    if scores.get("mobile", 100) < 50:
        insights.append(f"⚠️ Low mobile traffic — check mobile UX")

    # Geographic opportunity
    if countries:
        high_quality = [c for c in countries if "_error" not in c and c.get("quality_score", 0) > 2]
        if high_quality:
            best = max(high_quality, key=lambda x: x.get("quality_score", 0))
            insights.append(f"🟢 {best.get('country')} has highest quality traffic — consider localization")

    # No campaigns
    first = acq.get("first_touch", [])
    has_campaigns = any(f.get("firstUserCampaignName") not in [None, "(not set)", "(organic)", "(direct)"]
                       for f in first if "_error" not in f)
    if not has_campaigns:
        insights.append(f"📢 No tracked campaigns — add UTM parameters to links")

    print()
    if insights:
        for insight in insights:
            print(f"   {insight}")
    else:
        print("   ✅ Looking good! No critical issues detected.")

    # ===== FOOTER =====
    print(f"\n{'═'*80}")
    print(f"   ✅ DEEP DIVE v3 COMPLETE")
    print(f"{'═'*80}\n")


def save_snapshot(data: Dict, property_name: str, days: int):
    """Save snapshot for historical tracking."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{property_name}_{datetime.now().strftime('%Y-%m-%d_%H%M')}.json"
    filepath = SNAPSHOTS_DIR / filename

    # Slim down for storage
    snapshot = {
        "property": property_name,
        "generated": datetime.now().isoformat(),
        "days": days,
        "scores": data.get("scores", {}),
        "executive": data.get("executive", {}),
        "top_channels": data.get("acquisition", {}).get("channels", [])[:5],
        "top_countries": data.get("geography", {}).get("countries", [])[:10],
        "content_groups": data.get("content", {}).get("content_groups", {}),
    }

    with open(filepath, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    print(f"   💾 Snapshot: {filepath}")
