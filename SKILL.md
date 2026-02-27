# GA Deep Dive

Comprehensive Google Analytics 4 property analysis — extracts EVERYTHING the API offers.

**Battle-tested:** 609 lines, 22 sections, 26 API calls.

## Features

**374 dimensions, 95 metrics available.** This skill uses the important ones:

### Core Analysis
- **Real-time** active users
- **Core metrics**: sessions, users, engagement rate, bounce rate, duration, pages/session, events/session
- **User acquisition**: channel + source + medium breakdown with engagement
- **Referrer URLs**: exact URLs driving traffic
- **Landing pages**: entry points with bounce rates
- **All pages**: detailed performance metrics
- **All events**: complete event tracking with values

### Technology
- **Browsers & OS**: Chrome, Safari, Firefox with engagement by OS
- **Devices**: desktop, mobile, tablet breakdown
- **Screen resolutions**: what screens users have

### Geography & Time
- **Countries & cities**: with regions and engagement
- **Hour of day**: traffic patterns by hour (UTC)
- **Day of week**: weekday vs weekend patterns
- **Languages**: user language distribution

### User Behavior
- **New vs returning**: behavior differences
- **Daily trends**: session trends over time period
- **High bounce pages**: where users leave
- **User activity**: DAU/WAU/MAU ratios

### Health Scores
- **Engagement** (engagement rate + duration)
- **Traffic Diversity** (not too reliant on one channel)
- **Mobile Ready** (mobile traffic presence)
- **Content** (pages per session)
- **Growth** (trend analysis)

## Setup

```bash
cd ~/development/ga-deep-dive
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### First-time Auth (headless server)

1. Create OAuth credentials in Google Cloud Console
2. Place `credentials.json` at `~/.config/ga-deep-dive/credentials.json`
3. Run auth helper:
```bash
# Generate auth URL
python3 -c "
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
flow = InstalledAppFlow.from_client_secrets_file(
    str(Path.home() / '.config/ga-deep-dive/credentials.json'),
    ['https://www.googleapis.com/auth/analytics.readonly']
)
flow.redirect_uri = 'http://localhost:8085/'
auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
print(f'Open this URL:\n{auth_url}')
"
```
4. Open URL in browser, approve, copy redirect URL
5. Extract code and exchange:
```bash
python3 -c "
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
flow = InstalledAppFlow.from_client_secrets_file(
    str(Path.home() / '.config/ga-deep-dive/credentials.json'),
    ['https://www.googleapis.com/auth/analytics.readonly']
)
flow.redirect_uri = 'http://localhost:8085/'
flow.fetch_token(code='YOUR_CODE_HERE')
token_path = Path.home() / '.config/ga-deep-dive/token.json'
token_path.write_text(flow.credentials.to_json())
print('✅ Token saved')
"
```

## Usage

```bash
# Activate venv
source ~/development/ga-deep-dive/.venv/bin/activate

# Analyze by property name
python3 scripts/deep_dive.py solvr

# Analyze by property ID
python3 scripts/deep_dive.py 523300499

# Custom time period
python3 scripts/deep_dive.py solvr --days 60

# List known properties
python3 scripts/deep_dive.py --list
```

## Known Properties

Edit `PROPERTIES` dict in `deep_dive.py`:
```python
PROPERTIES = {
    'solvr': '523300499',
    'abecmed': '291040306',
    'sonus': '517562144',
    'reiduchat': '470924960',
    # Add more...
}
```

## Output Sections

```
🟢 REAL-TIME              — Active users now
📊 CORE METRICS           — Sessions, users, engagement, bounce
🚦 USER ACQUISITION       — Channel + source + medium
🔗 REFERRERS              — Traffic source URLs
🚪 LANDING PAGES          — Entry points
📄 ALL PAGES              — Page performance
⚡ ALL EVENTS             — Event tracking
💻 TECHNOLOGY             — Browsers & OS
📱 SCREEN RESOLUTIONS     — Display sizes
🌍 GEOGRAPHY              — Countries & cities
🕐 TIME PATTERNS          — Hour of day
📅 DAY OF WEEK            — Weekday patterns
👤 NEW VS RETURNING       — User segments
🌐 LANGUAGES              — User languages
📈 DAILY TREND            — Session trends
🚪 HIGH BOUNCE PAGES      — Exit points
📈 USER ACTIVITY          — DAU/WAU/MAU
🏥 HEALTH SCORES          — 5 scored dimensions
💡 RECOMMENDATIONS        — Actionable insights
```

## Requirements

```
google-analytics-data>=0.16.0
google-auth-oauthlib>=1.0.0
google-auth>=2.0.0
```

## Troubleshooting

### Token expired
Delete `~/.config/ga-deep-dive/token.json` and re-auth.

### Permission denied
Make sure the Google account has access to the GA4 property.
Check property ID with `--list` or in GA4 Admin → Property Settings.

### Missing dimensions
Some dimensions require specific GA4 setup (e.g., ecommerce, custom dimensions).
The script handles missing data gracefully.

## API Constraints Discovered

- **10 metrics per request limit** — Queries with >10 metrics fail silently. Script splits large queries.
- **DAU/WAU/MAU ratios** — GA4 returns these relative to rolling windows, not your date range. Script calculates manually.
- **Conversions** — Only shows if events are marked as "key events" in GA4 Admin.
- **Campaign data** — Requires UTM parameters on inbound links.

## Changelog

### v2 (2026-02-16)
- Fixed: Core metrics blank (10-metric API limit)
- Fixed: DAU/MAU ratios showing >100%
- Fixed: Growth score hardcoded
- Added: Campaigns & UTM tracking section
- Added: Key Events / Conversions section
- Added: Conversions to core metrics
- Added: User engagement duration
- Improved: Week-over-week growth calculation
