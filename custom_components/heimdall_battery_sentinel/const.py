"""Constants for Heimdall Battery Sentinel."""

import logging

DOMAIN = "heimdall_battery_sentinel"
_LOGGER = logging.getLogger(DOMAIN)

# Default values
DEFAULT_THRESHOLD = 15
MIN_THRESHOLD = 5
MAX_THRESHOLD = 100
THRESHOLD_STEP = 5

# WebSocket command prefixes
WS_PREFIX = "heimdall"
WS_CMD_SUMMARY = f"{WS_PREFIX}/summary"
WS_CMD_LIST = f"{WS_PREFIX}/list"
WS_CMD_SUBSCRIBE = f"{WS_PREFIX}/subscribe"

# Tab names
TAB_LOW_BATTERY = "low_battery"
TAB_UNAVAILABLE = "unavailable"

# Sort directions
SORT_ASC = "asc"
SORT_DESC = "desc"

# Sort keys
SORT_KEY_FRIENDLY_NAME = "friendly_name"
SORT_KEY_AREA = "area"
SORT_KEY_BATTERY_LEVEL = "battery_level"
SORT_KEY_ENTITY_ID = "entity_id"

# Severity levels
SEVERITY_YELLOW = "yellow"
SEVERITY_ORANGE = "orange"
SEVERITY_RED = "red"

# Page size
DEFAULT_PAGE_SIZE = 100
