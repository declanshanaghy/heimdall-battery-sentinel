"""WebSocket API for Heimdall Battery Sentinel."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback

from .const import (
    DEFAULT_PAGE_SIZE,
    DOMAIN,
    SORT_ASC,
    SORT_DESC,
    SORT_KEY_AREA,
    SORT_KEY_BATTERY_LEVEL,
    SORT_KEY_ENTITY_ID,
    SORT_KEY_FRIENDLY_NAME,
    TAB_LOW_BATTERY,
    TAB_UNAVAILABLE,
    WS_CMD_LIST,
    WS_CMD_SUBSCRIBE,
    WS_CMD_SUMMARY,
)
from .store import get_store

_LOGGER = logging.getLogger(__name__)


def _register_connection(hass: HomeAssistant, connection: Any) -> None:
    """Register a connection for push notifications via store subscription."""
    store = get_store()
    
    @callback
    def _handle_store_notification(event: dict) -> None:
        """Handle store notifications and forward to websocket connection."""
        try:
            connection.send_message(event)
        except Exception:
            # Connection might be closed, unsubscribe to clean up
            store.unsubscribe(sub_id)
            _LOGGER.debug("WebSocket connection closed, unsubscribed from store")
    
    sub_id = store.subscribe(_handle_store_notification)
    # Store subscription ID on connection for cleanup
    connection._store_sub_id = sub_id
    _LOGGER.debug("WebSocket connection subscribed to store for push notifications")


def _unregister_connection(hass: HomeAssistant, connection: Any) -> None:
    """Unregister a connection when it closes."""
    store = get_store()
    sub_id = getattr(connection, '_store_sub_id', None)
    if sub_id:
        store.unsubscribe(sub_id)
        _LOGGER.debug("WebSocket connection unsubscribed from store")


def _validate_sort_params(data: dict) -> tuple[str | None, str | None]:
    """Validate sorting parameters."""
    sort_by = data.get("sort_by", SORT_KEY_FRIENDLY_NAME)
    sort_dir = data.get("sort_dir", SORT_ASC)
    
    valid_sort_keys = (
        SORT_KEY_FRIENDLY_NAME,
        SORT_KEY_AREA,
        SORT_KEY_BATTERY_LEVEL,
        SORT_KEY_ENTITY_ID,
    )
    
    if sort_by not in valid_sort_keys:
        return f"Invalid sort_by: {sort_by}. Must be one of: {valid_sort_keys}"
    
    if sort_dir not in (SORT_ASC, SORT_DESC):
        return f"Invalid sort_dir: {sort_dir}. Must be 'asc' or 'desc'"
    
    return None, None


def _sort_rows(rows: list[dict], sort_by: str, sort_dir: str) -> list[dict]:
    """Sort rows by the specified key."""
    reverse = sort_dir == SORT_DESC
    
    # Primary sort key
    def get_sort_value(row: dict) -> tuple:
        if sort_by == SORT_KEY_FRIENDLY_NAME:
            return (row.get("friendly_name", "").casefold(), "")
        elif sort_by == SORT_KEY_AREA:
            return (row.get("area", "") or "", "")
        elif sort_by == SORT_KEY_BATTERY_LEVEL:
            # Numeric values first, then textual
            numeric = row.get("battery_numeric")
            if numeric is not None:
                return (0, numeric)
            return (1, 0)
        elif sort_by == SORT_KEY_ENTITY_ID:
            return ("", row.get("entity_id", ""))
        return ("", "")
    
    # Sort by primary key, then entity_id as tie-breaker
    rows.sort(key=lambda r: (*get_sort_value(r), r.get("entity_id", "")), reverse=reverse)
    return rows


def ws_get_summary(hass: HomeAssistant, connection: Any, msg: dict) -> None:
    """Handle summary request."""
    store = get_store()
    
    connection.send_result(
        msg["id"],
        {
            "low_battery_count": store.get_count(TAB_LOW_BATTERY),
            "unavailable_count": store.get_count(TAB_UNAVAILABLE),
            "threshold": store.threshold,
        },
    )


def ws_get_list(hass: HomeAssistant, connection: Any, msg: dict) -> None:
    """Handle list request with pagination."""
    data = msg.get("data", {})
    tab = data.get("tab", TAB_LOW_BATTERY)
    offset = data.get("offset", 0)
    page_size = data.get("page_size", DEFAULT_PAGE_SIZE)
    client_version = data.get("dataset_version", 0)
    
    if tab not in (TAB_LOW_BATTERY, TAB_UNAVAILABLE):
        connection.send_error(msg["id"], "invalid_tab", f"Invalid tab: {tab}")
        return
    
    sort_error, _ = _validate_sort_params(data)
    if sort_error:
        connection.send_error(msg["id"], "invalid_params", sort_error)
        return
    
    store = get_store()
    server_version = store.get_version(tab)
    
    # Check if dataset was invalidated
    if client_version != server_version:
        connection.send_result(
            msg["id"],
            {
                "rows": [],
                "next_offset": None,
                "end": True,
                "dataset_version": server_version,
                "invalidated": True,
            },
        )
        return
    
    sort_by = data.get("sort_by", SORT_KEY_FRIENDLY_NAME)
    sort_dir = data.get("sort_dir", SORT_ASC)
    
    # Get and sort rows
    rows_dict = store.get_rows(tab)
    rows = _sort_rows(list(rows_dict.values()), sort_by, sort_dir)
    
    # Apply pagination
    paginated = rows[offset : offset + page_size]
    next_offset = offset + page_size if len(rows) > offset + page_size else None
    
    connection.send_result(
        msg["id"],
        {
            "rows": paginated,
            "next_offset": next_offset,
            "end": next_offset is None,
            "dataset_version": server_version,
            "invalidated": False,
        },
    )


@callback
def ws_subscribe(hass: HomeAssistant, connection: Any, msg: dict) -> None:
    """Handle subscription request."""
    # Register connection for push notifications
    _register_connection(hass, connection)
    
    # Send initial confirmation
    connection.send_result(msg["id"], {"subscribed": True})


def register_websocket_commands(hass: HomeAssistant) -> None:
    """Register all websocket commands."""
    ws_api = hass.components.websocket_api
    ws_api.register_command(WS_CMD_SUMMARY, ws_get_summary)
    ws_api.register_command(WS_CMD_LIST, ws_get_list)
    ws_api.register_command(WS_CMD_SUBSCRIBE, ws_subscribe)
    _LOGGER.info("WebSocket commands registered")
