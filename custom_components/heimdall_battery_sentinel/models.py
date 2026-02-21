"""Data models for battery monitoring."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .const import (
    SEVERITY_CRITICAL,
    SEVERITY_CRITICAL_ICON,
    SEVERITY_CRITICAL_RATIO_THRESHOLD,
    SEVERITY_NOTICE,
    SEVERITY_NOTICE_ICON,
    SEVERITY_ORANGE,
    SEVERITY_ORANGE_THRESHOLD,
    SEVERITY_RED,
    SEVERITY_RED_THRESHOLD,
    SEVERITY_WARNING,
    SEVERITY_WARNING_ICON,
    SEVERITY_WARNING_RATIO_THRESHOLD,
    SEVERITY_YELLOW,
    SORT_DIR_ASC,
    SORT_FIELD_BATTERY_LEVEL,
    SORT_FIELD_FRIENDLY_NAME,
)


@dataclass
class LowBatteryRow:
    """Represents a single low-battery entity row."""

    entity_id: str
    friendly_name: str
    battery_display: str  # e.g. "15%" or "low"
    battery_numeric: Optional[float] = None  # None for textual
    severity: Optional[str] = None  # "critical" | "warning" | "notice" | None
    severity_icon: Optional[str] = None  # MDI icon for severity (e.g. "mdi:battery-alert")
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    area: Optional[str] = None
    device_id: Optional[str] = None  # Per AC4: used for per-device filtering
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> dict:
        """Serialize to dictionary for websocket responses."""
        return {
            "entity_id": self.entity_id,
            "friendly_name": self.friendly_name,
            "battery_display": self.battery_display,
            "battery_numeric": self.battery_numeric,
            "severity": self.severity,
            "severity_icon": self.severity_icon,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "area": self.area,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class UnavailableRow:
    """Represents a single unavailable entity row."""

    entity_id: str
    friendly_name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    area: Optional[str] = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> dict:
        """Serialize to dictionary for websocket responses."""
        return {
            "entity_id": self.entity_id,
            "friendly_name": self.friendly_name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "area": self.area,
            "updated_at": self.updated_at.isoformat(),
        }


def compute_severity(battery_numeric: float) -> str:
    """Compute severity for a numeric battery level (deprecated - for legacy use).

    Args:
        battery_numeric: Battery percentage (0-100).

    Returns:
        Severity string: "red", "orange", or "yellow".
    """
    if battery_numeric <= SEVERITY_RED_THRESHOLD:
        return SEVERITY_RED
    if battery_numeric <= SEVERITY_ORANGE_THRESHOLD:
        return SEVERITY_ORANGE
    return SEVERITY_YELLOW


def compute_severity_ratio(battery_numeric: float, threshold: int) -> tuple[str, str]:
    """Compute severity for a numeric battery based on ratio (AC2: Story 2-3).

    Severity is based on ratio = (battery_level / threshold) * 100:
    - Critical: ratio 0-33 (inclusive) → red color + mdi:battery-alert icon
    - Warning: ratio 34-66 → orange color + mdi:battery-low icon
    - Notice: ratio 67-100 → yellow color + mdi:battery-medium icon

    Args:
        battery_numeric: Battery percentage (0-100).
        threshold: Battery percentage threshold (5-100).

    Returns:
        Tuple of (severity_name, icon_name):
        - ("critical", "mdi:battery-alert")
        - ("warning", "mdi:battery-low")
        - ("notice", "mdi:battery-medium")
    """
    if threshold <= 0:
        # Avoid division by zero
        return SEVERITY_CRITICAL, SEVERITY_CRITICAL_ICON

    ratio = (battery_numeric / threshold) * 100

    if ratio <= SEVERITY_CRITICAL_RATIO_THRESHOLD:
        return SEVERITY_CRITICAL, SEVERITY_CRITICAL_ICON
    if ratio <= SEVERITY_WARNING_RATIO_THRESHOLD:
        return SEVERITY_WARNING, SEVERITY_WARNING_ICON
    return SEVERITY_NOTICE, SEVERITY_NOTICE_ICON


def sort_low_battery_rows(
    rows: list[LowBatteryRow], sort_by: str, sort_dir: str
) -> list[LowBatteryRow]:
    """Sort a list of LowBatteryRow objects.

    Args:
        rows: List of rows to sort.
        sort_by: Field name to sort by.
        sort_dir: "asc" or "desc".

    Returns:
        Sorted list.
    """
    reverse = sort_dir != SORT_DIR_ASC
    if sort_by == SORT_FIELD_BATTERY_LEVEL:
        def key_fn(row: LowBatteryRow):
            primary = row.battery_numeric if row.battery_numeric is not None else 999.0
            return (primary, (row.friendly_name or "").casefold(), row.entity_id)
    elif sort_by == SORT_FIELD_FRIENDLY_NAME:
        def key_fn(row: LowBatteryRow):
            return ((row.friendly_name or "").casefold(), row.entity_id)
    elif sort_by == "area":
        def key_fn(row: LowBatteryRow):
            return ((row.area or "").casefold(), (row.friendly_name or "").casefold(), row.entity_id)
    elif sort_by == "manufacturer":
        def key_fn(row: LowBatteryRow):
            return ((row.manufacturer or "").casefold(), (row.friendly_name or "").casefold(), row.entity_id)
    else:
        def key_fn(row: LowBatteryRow):
            return ((row.friendly_name or "").casefold(), row.entity_id)

    return sorted(rows, key=key_fn, reverse=reverse)


def sort_unavailable_rows(
    rows: list[UnavailableRow], sort_by: str, sort_dir: str
) -> list[UnavailableRow]:
    """Sort a list of UnavailableRow objects.

    Args:
        rows: List of rows to sort.
        sort_by: Field name to sort by.
        sort_dir: "asc" or "desc".

    Returns:
        Sorted list.
    """
    reverse = sort_dir != SORT_DIR_ASC
    if sort_by == "updated_at":
        def key_fn(row: UnavailableRow):
            return (row.updated_at, (row.friendly_name or "").casefold(), row.entity_id)
    elif sort_by == SORT_FIELD_FRIENDLY_NAME:
        def key_fn(row: UnavailableRow):
            return ((row.friendly_name or "").casefold(), row.entity_id)
    elif sort_by == "area":
        def key_fn(row: UnavailableRow):
            return ((row.area or "").casefold(), (row.friendly_name or "").casefold(), row.entity_id)
    elif sort_by == "manufacturer":
        def key_fn(row: UnavailableRow):
            return ((row.manufacturer or "").casefold(), (row.friendly_name or "").casefold(), row.entity_id)
    else:
        def key_fn(row: UnavailableRow):
            return ((row.friendly_name or "").casefold(), row.entity_id)

    return sorted(rows, key=key_fn, reverse=reverse)
