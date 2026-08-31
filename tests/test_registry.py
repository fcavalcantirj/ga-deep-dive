import pytest

from gadeepdive import registry

CUSTOM_PROPERTIES = {
    "repo-atlas": {"ga4_property_id": "900100200", "gsc_site": "sc-domain:repo-atlas.dev"},
    "endpoint-gateway": {"ga4_property_id": "900100201"},
}


def test_get_property_returns_registered_entry():
    prop = registry.get_property("repo-atlas", properties=CUSTOM_PROPERTIES)
    assert prop == {"ga4_property_id": "900100200", "gsc_site": "sc-domain:repo-atlas.dev"}


def test_get_property_without_gsc_site_defaults_to_none():
    prop = registry.get_property("endpoint-gateway", properties=CUSTOM_PROPERTIES)
    assert prop["ga4_property_id"] == "900100201"
    assert prop["gsc_site"] is None


def test_unknown_property_raises_with_registered_names_listed():
    with pytest.raises(registry.UnknownPropertyError) as excinfo:
        registry.get_property("commit-tracker", properties=CUSTOM_PROPERTIES)
    message = str(excinfo.value)
    assert "commit-tracker" in message
    assert "repo-atlas" in message
    assert "endpoint-gateway" in message


def test_load_properties_reads_seeded_config_file():
    properties = registry.load_properties()
    assert set(properties) == {"esp-atlas", "abecmed", "solvr", "sonus"}
    assert properties["esp-atlas"]["ga4_property_id"] == "551132215"
    assert properties["esp-atlas"]["gsc_site"] == "sc-domain:esp-atlas.com"
    assert properties["abecmed"]["ga4_property_id"] == "291040306"
    assert properties["solvr"]["ga4_property_id"] == "523300499"
    assert properties["sonus"]["ga4_property_id"] == "517562144"


def test_get_property_defaults_to_seeded_config_file():
    prop = registry.get_property("esp-atlas")
    assert prop["ga4_property_id"] == "551132215"


def test_unknown_property_against_default_registry_lists_seeded_names():
    with pytest.raises(registry.UnknownPropertyError) as excinfo:
        registry.get_property("not-a-real-property")
    message = str(excinfo.value)
    for name in ("esp-atlas", "abecmed", "solvr", "sonus"):
        assert name in message
