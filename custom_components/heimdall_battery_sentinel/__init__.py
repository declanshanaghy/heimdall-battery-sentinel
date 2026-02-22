"""Heimdall Battery Sentinel - Home Assistant custom integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, _LOGGER

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Heimdall Battery Sentinel from a config entry."""
    _LOGGER.info("Setting up Heimdall Battery Sentinel integration")
    
    hass.data.setdefault(DOMAIN, {})
    
    # TODO: Initialize event subscriptions, store, and websocket handlers
    # This will be implemented in story 1-2
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("Heimdall Battery Sentinel integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Heimdall Battery Sentinel integration")
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data.pop(DOMAIN)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    _LOGGER.info("Reloading Heimdall Battery Sentinel integration")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
