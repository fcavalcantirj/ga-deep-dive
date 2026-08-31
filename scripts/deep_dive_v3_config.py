"""
GA4 DEEP DIVE v3 — CONFIG
Paths, scopes, and property/funnel registries shared across the v3 CLI.
"""

from pathlib import Path

# ============================================================================
# CONFIG
# ============================================================================

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
CONFIG_DIR = Path.home() / '.config' / 'ga-deep-dive'
TOKEN_PATH = CONFIG_DIR / 'token.json'
CREDENTIALS_PATH = CONFIG_DIR / 'credentials.json'
DATA_DIR = Path(__file__).parent.parent / 'data'
SNAPSHOTS_DIR = DATA_DIR / 'snapshots'

PROPERTIES = {
    'solvr': '523300499',
    'abecmed': '291040306',
    'sonus': '517562144',
    'reiduchat': '470924960',
    'caosfera': '485692354',
    'ttn': '513412902',
}

# Solvr funnel stages
SOLVR_FUNNEL = {
    'visit': ['/'],
    'explore': ['/feed', '/agents', '/problems', '/ideas'],
    'auth': ['/join', '/login'],
    'onboard': ['/auth/callback', '/settings/api-keys'],
    'engage': ['/settings/agents', '/connect/agent'],
    'create': ['/problems', '/ideas'],  # POST actions tracked via events
}
