---
name: ga-deep-dive
description: Comprehensive Google Analytics 4 analysis — extracts EVERYTHING the API offers. Health scores, scroll depth, cohorts, demographics, and more.
metadata:
  openclaw:
    emoji: "📊"
    requires:
      python: ">=3.10"
---

# GA4 Deep Dive 📊

**The Owner's War Room** — Everything GA4 can tell you about your product.

## What You Get

| Script | Purpose |
|--------|---------|
| `deep_dive_v3.py` | Executive summary with 7 health scores |
| `deep_dive_v4.py` | THE FULL MONTY — scroll depth, cohorts, demographics |
| `send_report_email.py` | Bi-weekly email reports |

### Health Scores
- **Engagement** — Are users engaged?
- **Traffic Diversity** — Too reliant on one channel?
- **Retention** — Do users come back? (DAU/MAU)
- **Growth** — Are you growing?
- **Content** — Any problem pages?
- **Mobile** — Mobile-ready?
- **Geo Diversity** — Global reach?

### Deep Analysis (v4)
- 📜 **Scroll Depth** — How far users actually READ
- 🔗 **Outbound Links** — Where users click out to
- 🔍 **Site Search** — What users search for
- 👥 **Demographics** — Age, gender, interests
- 🌐 **Search Console** — Organic search performance
- 📊 **Cohort Retention** — Week-over-week retention
- 🎯 **Audiences** — Custom audience performance

---

## Quick Start

**Ask your OpenClaw:**
> "Help me set up the ga-deep-dive skill for my website"

Your agent will guide you through:
1. Creating Google Cloud OAuth credentials
2. Getting your GA4 property ID
3. Running your first analysis

---

## Manual Setup

### 1. Install Dependencies

```bash
cd ~/.openclaw/skills/ga-deep-dive
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use existing)
3. Enable **Google Analytics Data API**
4. Create **OAuth 2.0 Client ID** (Desktop app)
5. Download JSON → save as `~/.config/ga-deep-dive/credentials.json`

### 3. Get Your GA4 Property ID

1. Open [Google Analytics](https://analytics.google.com/)
2. Go to **Admin** → **Property Settings**
3. Copy the **Property ID** (9-digit number)

### 4. First Run (Auth)

```bash
source ~/.openclaw/skills/ga-deep-dive/.venv/bin/activate
python3 scripts/deep_dive_v3.py YOUR_PROPERTY_ID
```

It will open a browser for OAuth consent. Approve and you're set!

---

## Usage

### Run Analysis

```bash
# By property ID
python3 scripts/deep_dive_v3.py 123456789

# By name (if configured)
python3 scripts/deep_dive_v3.py mysite

# Full monty
python3 scripts/deep_dive_v4.py 123456789

# Custom period
python3 scripts/deep_dive_v3.py mysite --days 60
```

### Configure Property Names

Edit `scripts/deep_dive_v3.py` and add to `PROPERTIES`:

```python
PROPERTIES = {
    'mysite': '123456789',
    'blog': '987654321',
}
```

### Email Reports

Edit `scripts/send_report_email.py`:
- Update `recipients` list
- Requires AgentMail API key in OpenClaw config

Set up cron for bi-weekly reports:
```bash
# Mondays & Thursdays at 9am
0 9 * * 1,4 cd ~/.openclaw/skills/ga-deep-dive && .venv/bin/python3 scripts/send_report_email.py
```

---

## GA4 Setup Tips

For best results, enable these in GA4 Admin:

| Feature | Where | Why |
|---------|-------|-----|
| Google Signals | Data Settings → Data Collection | Demographics |
| Search Console | Product Links → Search Console | Organic search data |
| Enhanced Measurement | Data Streams → Web → Enhanced | Scrolls, outbound clicks |
| Key Events | Events → Mark as key event | Track conversions |

---

## Example Output

```
🏥 HEALTH SCORES
   ✅ Engagement           ████████████████░░░░ 81/100
   ❌ Traffic Diversity    █████░░░░░░░░░░░░░░░ 27/100
   ✅ Mobile               ██████████████████░░ 90/100
   
   🎯 OVERALL: 66/100 (Grade B)

💡 ACTIONABLE INSIGHTS
   🔴 72% traffic from Direct — DIVERSIFY NOW
   🚨 Fix /agents/me/claim — 100% bounce rate
   🟢 China has highest quality traffic — consider localization
```

---

## Troubleshooting

**"Token expired"**
```bash
rm ~/.config/ga-deep-dive/token.json
# Run again to re-auth
```

**"No demographic data"**
- Enable Google Signals in GA4
- Need 50+ users per segment (privacy threshold)

**"No Search Console data"**
- Link Search Console in GA4 Admin → Product Links
- Wait 24-48h for data sync

---

## License

MIT — Built by [ClaudiusThePirateEmperor](https://solvr.dev/agents/agent_ClaudiusThePirateEmperor) 🏴‍☠️

Repository: https://github.com/fcavalcantirj/ga-deep-dive
