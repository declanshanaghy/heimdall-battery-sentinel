"""Data models for Heimdall Battery Sentinel."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal


class Severity(str, Enum):
    """Severity level for battery status."""
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


@dataclass
class LowBatteryRow:
    """Row model for low battery entities."""
    entity_id: str
    friendly_name: str
    manufacturer: str | None
    model: str | None
    area: str | None
    battery_display: str
    battery_numeric: float | None
    severity: Severity | None
    updated_at: datetime


@dataclass
class UnavailableRow:
    """Row model for unavailable entities."""
    entity_id: str
    friendly_name: str
    manufacturer: str | None
    model: str | None
    area: str | None
    updated_at: datetime


# Type alias for tab names
TabType = Literal["low_battery", "unavailable"]
