"""Property registry: name -> {ga4_property_id, gsc_site}.

Registry is data (config/properties.json), not code — adding a property is a
config edit, never a code change.
"""

import json
from pathlib import Path
from typing import Dict, Optional

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "properties.json"


class UnknownPropertyError(ValueError):
    """Raised when a property name is not found in the registry."""

    def __init__(self, name: str, registered_names):
        names = ", ".join(sorted(registered_names))
        super().__init__(f"Unknown property '{name}'. Registered properties: {names}")
        self.name = name
        self.registered_names = sorted(registered_names)


def load_properties(path: Optional[Path] = None) -> Dict[str, dict]:
    """Load the property registry from a JSON config file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    with config_path.open() as f:
        return json.load(f)


def get_property(name: str, properties: Optional[Dict[str, dict]] = None) -> Dict[str, Optional[str]]:
    """Resolve a property name to {ga4_property_id, gsc_site}.

    Raises UnknownPropertyError listing registered names when `name` isn't found.
    """
    if properties is None:
        properties = load_properties()
    if name not in properties:
        raise UnknownPropertyError(name, properties.keys())
    entry = properties[name]
    return {
        "ga4_property_id": entry["ga4_property_id"],
        "gsc_site": entry.get("gsc_site"),
    }
