"""
GA4 DEEP DIVE v2 — CONFIG
Paths, scopes, and property/content-group registries shared across the v2 CLI.
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

# Solvr-specific content groups
SOLVR_CONTENT_GROUPS = {
    'agents': ['/agents', '/agents/'],
    'problems': ['/problems', '/problem/'],
    'ideas': ['/ideas', '/idea/'],
    'questions': ['/questions', '/question/'],
    'feed': ['/feed'],
    'auth': ['/login', '/join', '/auth/'],
    'settings': ['/settings'],
    'api': ['/api-docs', '/api'],
    'home': ['/'],
}
