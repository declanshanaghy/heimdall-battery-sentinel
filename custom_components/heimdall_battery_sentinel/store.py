"""In-memory data store for Heimdall Battery Sentinel."""

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from .models import LowBatteryRow, UnavailableRow, TabType


@dataclass
class DatasetState:
    """State for a single dataset (low_battery or unavailable)."""
    version: int = 0
    rows_by_id: dict[str, LowBatteryRow | UnavailableRow] = field(default_factory=dict)


@dataclass
class Store:
    """In-memory store for derived entity data."""
    threshold: int = 15
    low_battery: DatasetState = field(default_factory=DatasetState)
    unavailable: DatasetState = field(default_factory=DatasetState)
    _subscribers: dict[str, Callable[[dict], None]] = field(default_factory=dict)
    
    def increment_version(self, tab: TabType) -> None:
        """Increment dataset version for the given tab."""
        if tab == "low_battery":
            self.low_battery.version += 1
        else:
            self.unavailable.version += 1
    
    def get_version(self, tab: TabType) -> int:
        """Get current dataset version for the tab."""
        if tab == "low_battery":
            return self.low_battery.version
        return self.unavailable.version
    
    def get_rows(self, tab: TabType) -> dict[str, LowBatteryRow | UnavailableRow]:
        """Get all rows for a tab."""
        if tab == "low_battery":
            return self.low_battery.rows_by_id
        return self.unavailable.rows_by_id
    
    def set_rows(self, tab: TabType, rows: dict[str, LowBatteryRow | UnavailableRow]) -> None:
        """Set all rows for a tab."""
        if tab == "low_battery":
            self.low_battery.rows_by_id = rows
        else:
            self.unavailable.rows_by_id = rows
    
    def upsert_row(self, tab: TabType, row: LowBatteryRow | UnavailableRow) -> None:
        """Insert or update a row."""
        if tab == "low_battery":
            self.low_battery.rows_by_id[row.entity_id] = row
        else:
            self.unavailable.rows_by_id[row.entity_id] = row
    
    def remove_row(self, tab: TabType, entity_id: str) -> bool:
        """Remove a row. Returns True if row was removed."""
        if tab == "low_battery":
            if entity_id in self.low_battery.rows_by_id:
                del self.low_battery.rows_by_id[entity_id]
                return True
        else:
            if entity_id in self.unavailable.rows_by_id:
                del self.unavailable.rows_by_id[entity_id]
                return True
        return False
    
    def get_count(self, tab: TabType) -> int:
        """Get row count for a tab."""
        return len(self.get_rows(tab))
    
    def subscribe(self, callback: Callable[[dict], None]) -> str:
        """Subscribe to store changes. Returns subscription ID."""
        sub_id = str(uuid.uuid4())
        self._subscribers[sub_id] = callback
        return sub_id
    
    def unsubscribe(self, sub_id: str) -> None:
        """Unsubscribe from store changes."""
        self._subscribers.pop(sub_id, None)
    
    def notify_subscribers(self, event: dict) -> None:
        """Notify all subscribers of a change."""
        for callback in self._subscribers.values():
            try:
                callback(event)
            except Exception:
                pass  # Log but don't break other subscribers


# Global store instance
_store = Store()


def get_store() -> Store:
    """Get the global store instance."""
    return _store
