"""WebSocket API commands for heimdall_battery_sentinel."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import (
    DEFAULT_PAGE_SIZE,
    DOMAIN,
    SORT_DIR_ASC,
    SORT_FIELDS_LOW_BATTERY,
    SORT_FIELDS_UNAVAILABLE,
    SORT_FIELD_BATTERY_LEVEL,
    SORT_FIELD_FRIENDLY_NAME,
    TAB_LOW_BATTERY,
    TAB_UNAVAILABLE,
    VALID_SORT_DIRS,
    VALID_TABS,
    WS_COMMAND_LIST,
    WS_COMMAND_SUBSCRIBE,
    WS_COMMAND_SUMMARY,
    DATA_STORE,
)
from .store import HeimdallStore

_LOGGER = logging.getLogger(__name__)


def _get_store(hass: HomeAssistant) -> HeimdallStore:
    """Retrieve the HeimdallStore from hass.data.

    Args:
        hass: Home Assistant instance.

    Returns:
        HeimdallStore instance.

    Raises:
        KeyError: If integration is not set up.
    """
    return hass.data[DOMAIN][DATA_STORE]


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_COMMAND_SUMMARY,
    }
)
@websocket_api.async_response
async def ws_handle_summary(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Handle heimdall/summary websocket command.

    Returns counts, threshold, and dataset versions.

    Args:
        hass: Home Assistant instance.
        connection: Active WebSocket connection.
        msg: Incoming message dict (must include "id" and "type").
    """
    try:
        store = _get_store(hass)
        summary = store.get_summary()
        connection.send_result(msg["id"], summary)
        _LOGGER.debug("ws_handle_summary responded: %s", summary)
    except KeyError:
        connection.send_error(
            msg["id"],
            "not_initialized",
            f"Integration {DOMAIN} is not initialized",
        )
    except Exception:
        _LOGGER.exception("Unexpected error in ws_handle_summary")
        connection.send_error(
            msg["id"],
            "unknown_error",
            "An unexpected error occurred",
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_COMMAND_LIST,
        vol.Required("tab"): vol.In(VALID_TABS),
        vol.Optional("sort_by"): str,
        vol.Optional("sort_dir", default=SORT_DIR_ASC): vol.In(VALID_SORT_DIRS),
        vol.Optional("offset", default=0): vol.All(int, vol.Range(min=0)),
        vol.Optional("page_size", default=DEFAULT_PAGE_SIZE): vol.All(
            int, vol.Range(min=1, max=DEFAULT_PAGE_SIZE)
        ),
        vol.Optional("dataset_version"): int,
    }
)
@websocket_api.async_response
async def ws_handle_list(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Handle heimdall/list websocket command.

    Returns a sorted, paginated list of rows for the given tab.

    Args:
        hass: Home Assistant instance.
        connection: Active WebSocket connection.
        msg: Incoming message dict with tab, sort_by, sort_dir, offset, page_size,
             dataset_version fields.
    """
    tab = msg["tab"]
    sort_dir = msg.get("sort_dir", SORT_DIR_ASC)
    offset = msg.get("offset", 0)
    page_size = msg.get("page_size", DEFAULT_PAGE_SIZE)
    client_version = msg.get("dataset_version")

    # Default sort_by per tab
    if "sort_by" not in msg:
        sort_by = SORT_FIELD_BATTERY_LEVEL if tab == TAB_LOW_BATTERY else SORT_FIELD_FRIENDLY_NAME
    else:
        sort_by = msg["sort_by"]

    # Validate sort_by per tab
    valid_fields = SORT_FIELDS_LOW_BATTERY if tab == TAB_LOW_BATTERY else SORT_FIELDS_UNAVAILABLE
    if sort_by not in valid_fields:
        connection.send_error(
            msg["id"],
            "invalid_format",
            f"sort_by must be one of: {', '.join(sorted(valid_fields))}",
        )
        return

    try:
        store = _get_store(hass)
        result = store.get_page(
            tab=tab,
            sort_by=sort_by,
            sort_dir=sort_dir,
            offset=offset,
            page_size=page_size,
            client_version=client_version,
        )
        connection.send_result(msg["id"], result)
        _LOGGER.debug(
            "ws_handle_list tab=%s offset=%d returned %d rows (end=%s)",
            tab, offset, len(result["rows"]), result["end"],
        )
    except KeyError:
        connection.send_error(
            msg["id"],
            "not_initialized",
            f"Integration {DOMAIN} is not initialized",
        )
    except ValueError as exc:
        connection.send_error(msg["id"], "invalid_format", str(exc))
    except Exception:
        _LOGGER.exception("Unexpected error in ws_handle_list")
        connection.send_error(msg["id"], "unknown_error", "An unexpected error occurred")


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_COMMAND_SUBSCRIBE,
    }
)
@websocket_api.async_response
async def ws_handle_subscribe(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Handle heimdall/subscribe websocket command.

    Registers the connection for push updates from the store.
    Pushes: upsert, remove, summary, and invalidated events.

    Args:
        hass: Home Assistant instance.
        connection: Active WebSocket connection.
        msg: Incoming message dict.
    """
    try:
        store = _get_store(hass)
    except KeyError:
        connection.send_error(
            msg["id"],
            "not_initialized",
            f"Integration {DOMAIN} is not initialized",
        )
        return

    msg_id = msg["id"]

    @callback
    def on_store_event(event: dict) -> None:
        """Forward store events to the websocket connection."""
        try:
            connection.send_event(msg_id, event)
        except Exception:
            _LOGGER.debug("Failed to send store event to subscriber (connection closed?)")

    unsubscribe = store.subscribe(on_store_event)

    # ACK subscription
    connection.send_result(msg_id, {"subscribed": True})

    # Clean up when the connection closes
    connection.subscriptions[msg_id] = unsubscribe

    _LOGGER.debug("ws_handle_subscribe: subscription registered for msg_id=%d", msg_id)


def async_register_commands(hass: HomeAssistant) -> None:
    """Register all websocket commands with HA.

    Args:
        hass: Home Assistant instance.
    """
    websocket_api.async_register_command(hass, ws_handle_summary)
    websocket_api.async_register_command(hass, ws_handle_list)
    websocket_api.async_register_command(hass, ws_handle_subscribe)
    _LOGGER.debug(
        "Registered websocket commands: %s, %s, %s",
        WS_COMMAND_SUMMARY,
        WS_COMMAND_LIST,
        WS_COMMAND_SUBSCRIBE,
    )
