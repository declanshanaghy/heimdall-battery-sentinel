"""Data models for battery monitoring."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .const import (
    SEVERITY_ORANGE,
    SEVERITY_ORANGE_THRESHOLD,
    SEVERITY_RED,
    SEVERITY_RED_THRESHOLD,
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
    severity: Optional[str] = None  # "red" | "orange" | "yellow" | None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    area: Optional[str] = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> dict:
        """Serialize to dictionary for websocket responses."""
        return {
            "entity_id": self.entity_id,
            "friendly_name": self.friendly_name,
            "battery_display": self.battery_display,
            "battery_numeric": self.battery_numeric,
            "severity": self.severity,
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
    """Compute severity for a numeric battery level.

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


def sort_key_low_battery(row: LowBatteryRow, sort_by: str, sort_dir: str):
    """Return a sort key tuple for a LowBatteryRow.

    Stable tie-breaker: friendly_name (casefolded), then entity_id.
    """
    reverse = sort_dir != SORT_DIR_ASC
    if sort_by == SORT_FIELD_BATTERY_LEVEL:
        # Textual "low" sorts after numeric; use 999 as sentinel
        primary = row.battery_numeric if row.battery_numeric is not None else 999.0
    elif sort_by == SORT_FIELD_FRIENDLY_NAME:
        primary = (row.friendly_name or "").casefold()
    elif sort_by == "area":
        primary = (row.area or "").casefold()
    elif sort_by == "manufacturer":
        primary = (row.manufacturer or "").casefold()
    else:
        primary = (row.friendly_name or "").casefold()

    tie1 = (row.friendly_name or "").casefold()
    tie2 = row.entity_id

    if reverse:
        # Return negated values for numeric, or use the key passed through reversed=True
        return (-primary if isinstance(primary, float) else primary, tie1, tie2)
    return (primary, tie1, tie2)


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
