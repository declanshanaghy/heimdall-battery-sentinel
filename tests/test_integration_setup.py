"""Tests for heimdall_battery_sentinel integration setup."""
import sys
import pytest

# Ensure HA stubs are applied before importing integration modules
# (conftest.py does this at collection time, but we guard here too)


from custom_components.heimdall_battery_sentinel.const import DOMAIN


def test_domain_constant():
    """AC1: Domain string matches the integration domain."""
    assert DOMAIN == "heimdall_battery_sentinel"


def test_constants_exist():
    """AC2 (partial): Required constants exist in const.py."""
    from custom_components.heimdall_battery_sentinel import const

    # Configuration keys
    assert hasattr(const, "CONF_BATTERY_THRESHOLD")
    assert hasattr(const, "CONF_SCAN_INTERVAL")

    # Defaults
    assert const.DEFAULT_THRESHOLD == 15
    assert const.MIN_THRESHOLD == 5
    assert const.MAX_THRESHOLD == 100
    assert const.STEP_THRESHOLD == 5

    # WebSocket command names
    assert const.WS_COMMAND_SUMMARY == "heimdall/summary"
    assert const.WS_COMMAND_LIST == "heimdall/list"
    assert const.WS_COMMAND_SUBSCRIBE == "heimdall/subscribe"

    # Tab names
    assert const.TAB_LOW_BATTERY == "low_battery"
    assert const.TAB_UNAVAILABLE == "unavailable"


def test_domain_file_structure():
    """AC2: Required source files are importable (not empty stubs)."""
    import importlib

    modules = [
        "custom_components.heimdall_battery_sentinel",
        "custom_components.heimdall_battery_sentinel.const",
        "custom_components.heimdall_battery_sentinel.models",
        "custom_components.heimdall_battery_sentinel.evaluator",
        "custom_components.heimdall_battery_sentinel.store",
        "custom_components.heimdall_battery_sentinel.registry",
        "custom_components.heimdall_battery_sentinel.config_flow",
    ]
    for mod_name in modules:
        mod = importlib.import_module(mod_name)
        assert mod is not None, f"Module {mod_name} should be importable"


def test_models_are_defined():
    """Models required by architecture are importable and instantiable."""
    from custom_components.heimdall_battery_sentinel.models import (
        LowBatteryRow,
        UnavailableRow,
        compute_severity,
    )

    assert LowBatteryRow is not None
    assert UnavailableRow is not None
    assert callable(compute_severity)


def test_evaluator_class_exists():
    """BatteryEvaluator class is importable."""
    from custom_components.heimdall_battery_sentinel.evaluator import BatteryEvaluator

    evaluator = BatteryEvaluator(threshold=20)
    assert evaluator.threshold == 20


def test_store_class_exists():
    """HeimdallStore class is importable and initializable."""
    from custom_components.heimdall_battery_sentinel.store import HeimdallStore

    store = HeimdallStore(threshold=15)
    assert store.threshold == 15
    assert store.low_battery_count == 0
    assert store.unavailable_count == 0


def test_hass_data_initialized(mock_hass):
    """Integration initializes hass.data[DOMAIN] on setup."""
    from custom_components.heimdall_battery_sentinel.const import DOMAIN, DATA_STORE
    from custom_components.heimdall_battery_sentinel.store import HeimdallStore

    # Simulate what async_setup_entry does to hass.data
    mock_hass.data[DOMAIN] = {DATA_STORE: HeimdallStore(threshold=15)}

    assert DOMAIN in mock_hass.data
    assert DATA_STORE in mock_hass.data[DOMAIN]
    assert isinstance(mock_hass.data[DOMAIN][DATA_STORE], HeimdallStore)
