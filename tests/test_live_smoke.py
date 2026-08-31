"""One opt-in live smoke test: hits real Composio for esp-atlas to catch API
drift. Skipped unless GADD_LIVE=1 — never runs in normal CI/coverage runs."""

import json
import os

import pytest

from gadeepdive import cli

pytestmark = pytest.mark.skipif(os.environ.get("GADD_LIVE") != "1", reason="opt-in live test — set GADD_LIVE=1 to run")


def test_deep_dive_esp_atlas_via_composio(capsys):
    exit_code = cli.main(["esp-atlas", "--json"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["property"] == "esp-atlas"
    assert "active_users" in payload["live_now"]
    assert "sessions" in payload["executive_summary"]["current"]
    assert set(payload["health"]["scores"]) == {
        "Growth",
        "Content",
        "Engagement",
        "Mobile",
        "Geo Diversity",
        "Retention",
        "Traffic Diversity",
    }
