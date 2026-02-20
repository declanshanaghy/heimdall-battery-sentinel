"""Test integration setup."""
from unittest.mock import patch

from homeassistant.setup import async_setup_component

from custom_components.heimdall_battery_sentinel.const import DOMAIN


async def test_setup(hass):
    """Test that the integration is set up correctly."""
    # Ensure integration loads without errors
    assert await async_setup_component(hass, DOMAIN, {}) is True
    
    # Verify our domain is registered
    assert DOMAIN in hass.data
    
    # Check that our logger was initialized
    logs = hass.states.async_all("sensor")
    assert any(log.entity_id.startswith(f"sensor.{DOMAIN}") for log in logs)