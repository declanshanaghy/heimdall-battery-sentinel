"""The heimdall_battery_sentinel integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import panel_custom

from .const import (
    CONF_BATTERY_THRESHOLD,
    DATA_REGISTRY,
    DATA_STORE,
    DATA_WS_SUBSCRIPTIONS,
    DEFAULT_THRESHOLD,
    DOMAIN,
)
from .evaluator import BatteryEvaluator
from .registry import MetadataResolver, get_metadata_fn
from .store import HeimdallStore
from .websocket import async_register_commands

LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the heimdall_battery_sentinel component from YAML (legacy).

    This integration uses config entries; YAML setup is a no-op.

    Args:
        hass: Home Assistant instance.
        config: YAML configuration dict.

    Returns:
        True always (integration loads via config entries).
    """
    LOGGER.info("heimdall_battery_sentinel: async_setup called (config entries manage setup)")
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up heimdall_battery_sentinel from a config entry.

    Per ADR-002: initializes in-memory store, evaluator, metadata resolver,
    subscribes to HA state/entity events, and performs initial cache population.

    Args:
        hass: Home Assistant instance.
        entry: The config entry with user-configured options.

    Returns:
        True if setup succeeded.
    """
    LOGGER.info("heimdall_battery_sentinel: async_setup_entry called for entry_id=%s", entry.entry_id)

    # Ensure domain namespace exists
    hass.data.setdefault(DOMAIN, {})

    # Read threshold from config entry options (fallback to data, then default)
    threshold = entry.options.get(
        CONF_BATTERY_THRESHOLD,
        entry.data.get(CONF_BATTERY_THRESHOLD, DEFAULT_THRESHOLD),
    )
    LOGGER.debug("Using battery threshold: %d%%", threshold)

    # Initialize core components
    store = HeimdallStore(threshold=threshold)
    resolver = MetadataResolver(hass)
    evaluator = BatteryEvaluator(threshold=threshold)

    # Store runtime objects so websocket handlers can access them
    hass.data[DOMAIN] = {
        DATA_STORE: store,
        DATA_REGISTRY: resolver,
        DATA_WS_SUBSCRIPTIONS: [],
    }

    # Register WebSocket API commands
    async_register_commands(hass)

    # Register custom panel
    # Register static path for the panel JS
    hass.http.async_register_static_paths(
        [{"type": "module", "path": hass.config.path("custom_components/heimdall_battery_sentinel/www/panel-heimdall.js"), "url_path": "local/heimdall_battery_sentinel/panel-heimdall.js"}]
    )
    panel_custom.async_register_panel(
        component_name="iframe",
        sidebar_title="Battery Sentinel",
        sidebar_icon="mdi:battery",
        frontend_url_path="heimdall-battery-sentinel",
        html_url="/local/heimdall_battery_sentinel/panel-heimdall.html",
        require_admin=False,
    )

    # Perform initial dataset population from current HA states
    await _populate_initial_datasets(hass, store, evaluator, resolver)

    # Subscribe to state change events for incremental updates
    entry.async_on_unload(
        hass.bus.async_listen(
            "state_changed",
            lambda event: _handle_state_changed(hass, store, evaluator, resolver, event),
        )
    )

    # Subscribe to registry update events to invalidate metadata cache
    # Per ADR-006: Metadata cache must be invalidated when registries change
    entry.async_on_unload(
        hass.bus.async_listen(
            "device_registry_updated",
            lambda event: _handle_registry_updated(resolver),
        )
    )
    entry.async_on_unload(
        hass.bus.async_listen(
            "area_registry_updated",
            lambda event: _handle_registry_updated(resolver),
        )
    )
    entry.async_on_unload(
        hass.bus.async_listen(
            "entity_registry_updated",
            lambda event: _handle_registry_updated(resolver),
        )
    )

    # Listen for config entry options updates (threshold changes)
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    LOGGER.info("heimdall_battery_sentinel: setup complete (low_battery=%d, unavailable=%d)",
                store.low_battery_count, store.unavailable_count)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a heimdall_battery_sentinel config entry.

    Cleans up runtime objects from hass.data.

    Args:
        hass: Home Assistant instance.
        entry: The config entry being unloaded.

    Returns:
        True if unload succeeded.
    """
    LOGGER.info("heimdall_battery_sentinel: async_unload_entry called for entry_id=%s", entry.entry_id)
    hass.data.pop(DOMAIN, None)
    return True


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates (e.g., threshold change via options flow).

    Reloads the config entry to apply new options.

    Args:
        hass: Home Assistant instance.
        entry: Updated config entry.
    """
    LOGGER.info("heimdall_battery_sentinel: options updated; reloading entry")
    await hass.config_entries.async_reload(entry.entry_id)


async def _populate_initial_datasets(
    hass: HomeAssistant,
    store: HeimdallStore,
    evaluator: BatteryEvaluator,
    resolver: MetadataResolver,
) -> None:
    """Populate store with an initial snapshot of all HA states.

    Args:
        hass: Home Assistant instance.
        store: HeimdallStore to populate.
        evaluator: BatteryEvaluator instance.
        resolver: MetadataResolver instance.
    """
    all_states = hass.states.async_all()
    metadata_fn = get_metadata_fn(resolver)
    low_battery_rows, unavailable_rows = evaluator.batch_evaluate(all_states, metadata_fn)

    store.bulk_set_low_battery(low_battery_rows)
    store.bulk_set_unavailable(unavailable_rows)

    LOGGER.debug(
        "Initial dataset: %d low-battery entities, %d unavailable entities",
        len(low_battery_rows),
        len(unavailable_rows),
    )


def _handle_registry_updated(resolver: MetadataResolver) -> None:
    """Handle registry update events and invalidate metadata cache.

    Per ADR-006: When device, area, or entity registries change,
    the metadata cache must be invalidated so that subsequent resolves
    pick up the latest metadata.

    Args:
        resolver: MetadataResolver instance to invalidate.
    """
    LOGGER.debug("Registry updated event detected; invalidating metadata cache")
    resolver.invalidate_cache()


def _handle_state_changed(
    hass: HomeAssistant,
    store: HeimdallStore,
    evaluator: BatteryEvaluator,
    resolver: MetadataResolver,
    event: Any,
) -> None:
    """Handle a HA state_changed event and update datasets incrementally.

    Args:
        hass: Home Assistant instance.
        store: HeimdallStore to update.
        evaluator: BatteryEvaluator instance.
        resolver: MetadataResolver instance.
        event: HA event object with data {"entity_id", "old_state", "new_state"}.
    """
    try:
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")

        if entity_id is None:
            return

        meta = resolver.resolve(entity_id)
        LOGGER.debug(f"Metadata for {entity_id}: unpacked {len(meta) if meta else 0} elements (expected 4)")
        if meta and len(meta) == 4:
            manufacturer, model, area, device_id = meta
        else:
            if meta and len(meta) != 4:
                LOGGER.warning(f"Metadata for {entity_id} has unexpected length: {len(meta) if meta else 0}, expected 4")
            manufacturer, model, area = meta if meta else (None, None, None)
            device_id = None

        # --- Low battery ---
        lb_row = evaluator.evaluate_low_battery(new_state, manufacturer, model, area)
        if lb_row is not None:
            lb_row.device_id = device_id
            store.upsert_low_battery(lb_row)
        else:
            store.remove_low_battery(entity_id)

        # --- Unavailable ---
        un_row = evaluator.evaluate_unavailable(new_state, manufacturer, model, area)
        if un_row is not None:
            store.upsert_unavailable(un_row)
        else:
            store.remove_unavailable(entity_id)
    except Exception as e:
        LOGGER.error(f"Error in state change handler: {e}", exc_info=True)
