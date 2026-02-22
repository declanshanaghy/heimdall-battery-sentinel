"""Heimdall Battery Sentinel - Home Assistant custom integration."""

import logging
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import event as ha_event

from .const import DOMAIN, TAB_LOW_BATTERY, TAB_UNAVAILABLE, _LOGGER
from .evaluator import evaluate_battery
from .models import LowBatteryRow, UnavailableRow
from .registry import get_registry_cache
from .store import get_store
from .websocket import register_websocket_commands

PLATFORMS = ["sensor"]

# Store unsub functions for cleanup
_unsubs = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Heimdall Battery Sentinel from a config entry."""
    _LOGGER.info("Setting up Heimdall Battery Sentinel integration")
    
    hass.data.setdefault(DOMAIN, {})
    
    # Initialize event subscriptions
    await _setup_event_listeners(hass)
    
    # Register websocket commands
    register_websocket_commands(hass)
    
    # Initial scan of all states
    await _initial_scan(hass)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("Heimdall Battery Sentinel integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Heimdall Battery Sentinel integration")
    
    # Unsubscribe from events
    for unsub in _unsubs:
        unsub()
    _unsubs.clear()
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data.pop(DOMAIN)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    _LOGGER.info("Reloading Heimdall Battery Sentinel integration")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def _process_state_change(
    hass: HomeAssistant,
    store: Any,
    registry_cache: Any,
    entity_id: str,
    old_state: Any,
    new_state: Any,
) -> None:
    """Process a state change and update the store."""
    # Determine what tabs might be affected
    # Battery entities have device_class = battery
    is_battery_entity = False
    if new_state and new_state.attributes:
        is_battery_entity = new_state.attributes.get("device_class") == "battery"
    elif old_state and old_state.attributes:
        is_battery_entity = old_state.attributes.get("device_class") == "battery"
    
    # Process for low battery tab if it's a battery entity
    if is_battery_entity:
        _update_low_battery_store(hass, store, registry_cache, entity_id, new_state)
    
    # Process for unavailable tab (any entity can become unavailable)
    _update_unavailable_store(hass, store, registry_cache, entity_id, new_state)


def _update_low_battery_store(
    hass: HomeAssistant,
    store: Any,
    registry_cache: Any,
    entity_id: str,
    state: Any,
) -> None:
    """Update low battery store for an entity."""
    if state is None:
        # Entity was removed - remove from store
        if store.remove_row(TAB_LOW_BATTERY, entity_id):
            store.increment_version(TAB_LOW_BATTERY, {
                "type": "remove",
                "tab": TAB_LOW_BATTERY,
                "entity_id": entity_id,
            })
        return
    
    # Check if entity has battery device class
    if state.attributes.get("device_class") != "battery":
        return
    
    # Evaluate battery state
    state_value = state.state
    unit = state.attributes.get("unit_of_measurement")
    threshold = store.threshold
    
    result = evaluate_battery(state_value, unit, threshold)
    
    if result["is_low"]:
        # Resolve metadata
        metadata = registry_cache.resolve_metadata(entity_id)
        friendly_name = state.attributes.get("friendly_name", entity_id)
        
        row = LowBatteryRow(
            entity_id=entity_id,
            friendly_name=friendly_name,
            manufacturer=metadata.get("manufacturer"),
            model=metadata.get("model"),
            area=metadata.get("area"),
            battery_display=result["display"],
            battery_numeric=result["numeric"],
            severity=result["severity"],
            updated_at=datetime.now(),
        )
        
        store.upsert_row(TAB_LOW_BATTERY, row)
        store.increment_version(TAB_LOW_BATTERY, {
            "type": "upsert",
            "tab": TAB_LOW_BATTERY,
            "row": row,
        })
    else:
        # Was previously low but no longer
        if store.remove_row(TAB_LOW_BATTERY, entity_id):
            store.increment_version(TAB_LOW_BATTERY, {
                "type": "remove",
                "tab": TAB_LOW_BATTERY,
                "entity_id": entity_id,
            })


def _update_unavailable_store(
    hass: HomeAssistant,
    store: Any,
    registry_cache: Any,
    entity_id: str,
    state: Any,
) -> None:
    """Update unavailable store for an entity."""
    if state is None:
        # Entity was removed - remove from store
        if store.remove_row(TAB_UNAVAILABLE, entity_id):
            store.increment_version(TAB_UNAVAILABLE, {
                "type": "remove",
                "tab": TAB_UNAVAILABLE,
                "entity_id": entity_id,
            })
        return
    
    # Check if unavailable
    if state.state == STATE_UNAVAILABLE:
        # Resolve metadata
        metadata = registry_cache.resolve_metadata(entity_id)
        friendly_name = state.attributes.get("friendly_name", entity_id)
        
        row = UnavailableRow(
            entity_id=entity_id,
            friendly_name=friendly_name,
            manufacturer=metadata.get("manufacturer"),
            model=metadata.get("model"),
            area=metadata.get("area"),
            updated_at=datetime.now(),
        )
        
        store.upsert_row(TAB_UNAVAILABLE, row)
        store.increment_version(TAB_UNAVAILABLE, {
            "type": "upsert",
            "tab": TAB_UNAVAILABLE,
            "row": row,
        })
    else:
        # Was previously unavailable but no longer
        if store.remove_row(TAB_UNAVAILABLE, entity_id):
            store.increment_version(TAB_UNAVAILABLE, {
                "type": "remove",
                "tab": TAB_UNAVAILABLE,
                "entity_id": entity_id,
            })


async def _setup_event_listeners(hass: HomeAssistant) -> None:
    """Set up Home Assistant event listeners."""
    store = get_store()
    registry_cache = get_registry_cache()
    
    @callback
    def _handle_state_changed(event: Event) -> None:
        """Handle state_changed event from HA."""
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        entity_id = event.data.get("entity_id")
        
        if not entity_id:
            return
        
        _process_state_change(
            hass, store, registry_cache, entity_id, old_state, new_state
        )
    
    @callback
    def _handle_entity_registry_updated(event: Event) -> None:
        """Handle entity registry update event."""
        _LOGGER.debug("Entity registry updated: %s", event.event_type)
        hass.async_create_task(_refresh_entity_metadata(hass))
    
    @callback
    def _handle_device_registry_updated(event: Event) -> None:
        """Handle device registry update event."""
        _LOGGER.debug("Device registry updated: %s", event.event_type)
        hass.async_create_task(_refresh_entity_metadata(hass))
    
    @callback
    def _handle_area_registry_updated(event: Event) -> None:
        """Handle area registry update event."""
        _LOGGER.debug("Area registry updated: %s", event.event_type)
        hass.async_create_task(_refresh_entity_metadata(hass))
    
    # Subscribe to state_changed events
    _unsubs.append(
        hass.bus.async_listen("state_changed", _handle_state_changed)
    )
    
    # Subscribe to registry update events
    _unsubs.append(
        hass.bus.async_listen("entity_registry_updated", _handle_entity_registry_updated)
    )
    _unsubs.append(
        hass.bus.async_listen("device_registry_updated", _handle_device_registry_updated)
    )
    _unsubs.append(
        hass.bus.async_listen("area_registry_updated", _handle_area_registry_updated)
    )
    
    _LOGGER.info("Event listeners registered")


async def _initial_scan(hass: HomeAssistant) -> None:
    """Perform initial scan of all states on startup."""
    store = get_store()
    registry_cache = get_registry_cache()
    
    # Update registry caches
    entity_registry = hass.helpers.entity_registry.async_get(hass)
    device_registry = hass.helpers.device_registry.async_get(hass)
    area_registry = hass.helpers.area_registry.async_get(hass)
    
    registry_cache.update_entities(entity_registry.entities.values())
    registry_cache.update_devices(device_registry.devices.values())
    registry_cache.update_areas(area_registry.areas.values())
    
    # Scan all states
    for entity_id, state in hass.states.all.items():
        _process_state_change(hass, store, registry_cache, entity_id, None, state)
    
    _LOGGER.info(
        "Initial scan complete: %d low battery, %d unavailable",
        store.get_count(TAB_LOW_BATTERY),
        store.get_count(TAB_UNAVAILABLE),
    )


async def _refresh_entity_metadata(hass: HomeAssistant) -> None:
    """Refresh entity metadata from registries and update affected rows."""
    store = get_store()
    registry_cache = get_registry_cache()
    
    # Update registry caches
    entity_registry = hass.helpers.entity_registry.async_get(hass)
    device_registry = hass.helpers.device_registry.async_get(hass)
    area_registry = hass.helpers.area_registry.async_get(hass)
    
    registry_cache.update_entities(entity_registry.entities.values())
    registry_cache.update_devices(device_registry.devices.values())
    registry_cache.update_areas(area_registry.areas.values())
    
    # Scan all states to update with new metadata
    for entity_id, state in hass.states.all.items():
        _process_state_change(hass, store, registry_cache, entity_id, None, state)
    
    store.increment_version(TAB_LOW_BATTERY, {
        "type": "invalidated",
        "tab": TAB_LOW_BATTERY,
        "dataset_version": store.get_version(TAB_LOW_BATTERY),
    })
    store.increment_version(TAB_UNAVAILABLE, {
        "type": "invalidated",
        "tab": TAB_UNAVAILABLE,
        "dataset_version": store.get_version(TAB_UNAVAILABLE),
    })
    
    _LOGGER.info("Entity metadata refreshed")
