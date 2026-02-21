"""Constants for the heimdall_battery_sentinel integration."""
from __future__ import annotations

DOMAIN = "heimdall_battery_sentinel"

# Configuration keys
CONF_BATTERY_THRESHOLD = "battery_threshold"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_THRESHOLD = 15
MIN_THRESHOLD = 5
MAX_THRESHOLD = 100
STEP_THRESHOLD = 5
DEFAULT_NAME = "Heimdall Battery Sentinel"

# Attribute keys
ATTR_BATTERY = "battery_level"
ATTR_BATTERY_DISPLAY = "battery_display"
ATTR_UNAVAILABLE = "unavailable"
ATTR_SEVERITY = "severity"

# Device class
DEVICE_CLASS_BATTERY = "battery"

# State constants
STATE_UNAVAILABLE = "unavailable"
STATE_LOW = "low"
STATE_MEDIUM = "medium"
STATE_HIGH = "high"
TEXTUAL_BATTERY_STATES = {STATE_LOW, STATE_MEDIUM, STATE_HIGH}
UNIT_PERCENT = "%"

# Severity levels
SEVERITY_RED = "red"
SEVERITY_ORANGE = "orange"
SEVERITY_YELLOW = "yellow"
SEVERITY_CRITICAL = "critical"
SEVERITY_WARNING = "warning"
SEVERITY_NOTICE = "notice"

# Severity thresholds (old absolute-based, kept for reference)
SEVERITY_RED_THRESHOLD = 5     # 0–5%
SEVERITY_ORANGE_THRESHOLD = 10  # 6–10%
# 11–threshold% → yellow

# Ratio-based severity thresholds (AC2: Story 2-3)
SEVERITY_CRITICAL_RATIO_THRESHOLD = 33  # ratio <= 33 → critical
SEVERITY_WARNING_RATIO_THRESHOLD = 66   # ratio <= 66 → warning
# ratio > 66 → notice

# Severity icons (Material Design Icons)
SEVERITY_CRITICAL_ICON = "mdi:battery-alert"
SEVERITY_WARNING_ICON = "mdi:battery-low"
SEVERITY_NOTICE_ICON = "mdi:battery-medium"

# WebSocket commands
WS_COMMAND_SUMMARY = "heimdall/summary"
WS_COMMAND_LIST = "heimdall/list"
WS_COMMAND_SUBSCRIBE = "heimdall/subscribe"

# Tab names
TAB_LOW_BATTERY = "low_battery"
TAB_UNAVAILABLE = "unavailable"
VALID_TABS = {TAB_LOW_BATTERY, TAB_UNAVAILABLE}

# Sort fields
SORT_FIELD_FRIENDLY_NAME = "friendly_name"
SORT_FIELD_AREA = "area"
SORT_FIELD_BATTERY_LEVEL = "battery_level"
SORT_FIELD_MANUFACTURER = "manufacturer"
SORT_FIELD_UPDATED_AT = "updated_at"

SORT_FIELDS_LOW_BATTERY = {
    SORT_FIELD_FRIENDLY_NAME,
    SORT_FIELD_AREA,
    SORT_FIELD_BATTERY_LEVEL,
    SORT_FIELD_MANUFACTURER,
}
SORT_FIELDS_UNAVAILABLE = {
    SORT_FIELD_FRIENDLY_NAME,
    SORT_FIELD_AREA,
    SORT_FIELD_MANUFACTURER,
    SORT_FIELD_UPDATED_AT,
}

SORT_DIR_ASC = "asc"
SORT_DIR_DESC = "desc"
VALID_SORT_DIRS = {SORT_DIR_ASC, SORT_DIR_DESC}

# Pagination
DEFAULT_PAGE_SIZE = 100

# Storage keys
STORAGE_KEY = f"{DOMAIN}_store"
STORAGE_VERSION = 1

# hass.data key for runtime data
DATA_STORE = "store"
DATA_REGISTRY = "registry"
DATA_WS_SUBSCRIPTIONS = "ws_subscriptions"

# Metadata display values for missing data (AC2, AC3 of story 3-2)
METADATA_UNKNOWN = "Unknown"
METADATA_UNASSIGNED = "Unassigned"
