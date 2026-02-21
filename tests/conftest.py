"""Test configuration for heimdall_battery_sentinel tests.

Provides lightweight mocks for Home Assistant objects so that unit tests
can run without a full HA installation.
"""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, AsyncMock

import pytest


# ---------------------------------------------------------------------------
# Stub out Home Assistant modules that aren't installed in the test venv.
# Tests that exercise pure-Python logic (models, evaluator, store) don't need
# the real HA runtime.  Integration-level tests that genuinely need HA are
# skipped if HA is not installed.
# ---------------------------------------------------------------------------

def _make_stub_module(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


def _ensure_ha_stubs() -> None:
    """Create minimal stubs for HA modules if not already installed."""
    if "homeassistant" in sys.modules:
        return  # Real HA is available; don't stub

    ha = _make_stub_module("homeassistant")
    ha.core = _make_stub_module("homeassistant.core")
    ha.config_entries = _make_stub_module("homeassistant.config_entries")
    ha.components = _make_stub_module("homeassistant.components")
    ha.components.websocket_api = _make_stub_module("homeassistant.components.websocket_api")
    ha.setup = _make_stub_module("homeassistant.setup")
    ha.helpers = _make_stub_module("homeassistant.helpers")
    ha.helpers.entity_registry = _make_stub_module("homeassistant.helpers.entity_registry")
    ha.helpers.device_registry = _make_stub_module("homeassistant.helpers.device_registry")
    ha.helpers.area_registry = _make_stub_module("homeassistant.helpers.area_registry")

    # Stub ConfigFlow base class — must accept `domain=` in __init_subclass__
    class _ConfigFlow:
        def __init_subclass__(cls, domain=None, **kwargs):
            super().__init_subclass__(**kwargs)

    class _OptionsFlow:
        pass

    config_entries = sys.modules["homeassistant.config_entries"]
    config_entries.ConfigFlow = _ConfigFlow
    config_entries.OptionsFlow = _OptionsFlow
    config_entries.ConfigEntry = MagicMock

    # Stub websocket_api decorators as pass-through
    ws_api = sys.modules["homeassistant.components.websocket_api"]
    ws_api.websocket_command = lambda schema: (lambda fn: fn)
    ws_api.async_response = lambda fn: fn
    ws_api.async_register_command = MagicMock()
    ws_api.ActiveConnection = MagicMock

    # Stub homeassistant.core.callback
    core = sys.modules["homeassistant.core"]
    core.callback = lambda fn: fn
    core.HomeAssistant = MagicMock

    # Stub async_setup_component
    setup = sys.modules["homeassistant.setup"]
    setup.async_setup_component = AsyncMock(return_value=True)


_ensure_ha_stubs()


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_hass():
    """Return a lightweight mock of a Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    hass.states.async_all.return_value = []
    hass.bus.async_listen.return_value = MagicMock()
    hass.config_entries.async_reload = AsyncMock()
    return hass


@pytest.fixture()
def mock_state():
    """Factory fixture for creating mock HA State objects."""
    def _make_state(entity_id, state, attributes=None):
        s = MagicMock()
        s.entity_id = entity_id
        s.state = state
        s.attributes = attributes or {}
        return s
    return _make_state
