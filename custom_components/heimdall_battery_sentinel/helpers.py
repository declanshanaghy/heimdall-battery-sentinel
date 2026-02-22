"""Helper functions for Heimdall Battery Sentinel."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry, device_registry, entity_registry


async def get_clusters(hass: HomeAssistant) -> dict:
    """Get clusters data (placeholder for future implementation)."""
    # This is a placeholder - will be implemented in later stories
    return {}


def get_entity_registry(hass: HomeAssistant) -> entity_registry.EntityRegistry:
    """Get the entity registry."""
    return entity_registry.async_get(hass)


def get_device_registry(hass: HomeAssistant) -> device_registry.DeviceRegistry:
    """Get the device registry."""
    return device_registry.async_get(hass)


def get_area_registry(hass: HomeAssistant) -> area_registry.AreaRegistry:
    """Get the area registry."""
    return area_registry.async_get(hass)
