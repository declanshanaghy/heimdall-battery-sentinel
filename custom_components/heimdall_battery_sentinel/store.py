"""In-memory data store for Heimdall Battery Sentinel."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Literal

from .const import (
    DEFAULT_PAGE_SIZE,
    SORT_ASC,
    SORT_DESC,
    SORT_KEY_BATTERY_LEVEL,
    SORT_KEY_ENTITY_ID,
    SORT_KEY_FRIENDLY_NAME,
    SORT_KEY_AREA,
    SORT_KEY_UPDATED_AT,
)
from .models import LowBatteryRow, Severity, TabType, UnavailableRow

SortKey = Literal["friendly_name", "area", "battery_level", "entity_id", "updated_at"]
SortDir = Literal["asc", "desc"]


def _get_sort_value(row: LowBatteryRow | UnavailableRow, sort_key: SortKey, sort_dir: SortDir = SORT_ASC) -> Any:
    """Get sort value for a row based on sort key."""
    if sort_key == SORT_KEY_FRIENDLY_NAME:
        # Case-fold friendly name for stable sorting
        return (row.friendly_name or "").casefold()
    elif sort_key == SORT_KEY_AREA:
        # Area can be None, sort None last
        return (row.area or "").casefold() if row.area else "\uffff"
    elif sort_key == SORT_KEY_BATTERY_LEVEL:
        # For LowBatteryRow, sort by numeric value; for UnavailableRow, use None
        if isinstance(row, LowBatteryRow):
            # None batteries sort last
            return row.battery_numeric if row.battery_numeric is not None else -1
        return -1
    elif sort_key == SORT_KEY_ENTITY_ID:
        return row.entity_id.casefold()
    elif sort_key == SORT_KEY_UPDATED_AT:
        # Sort by updated_at timestamp - None sorts last
        # Use datetime.max for ascending (so None comes last) and datetime.min for descending
        if row.updated_at is None:
            return datetime.max if sort_dir == SORT_ASC else datetime.min
        return row.updated_at
    return row.entity_id.casefold()


def _sort_rows(
    rows: list[LowBatteryRow | UnavailableRow],
    sort_key: SortKey,
    sort_dir: SortDir,
) -> list[LowBatteryRow | UnavailableRow]:
    """Sort rows by sort key and direction."""
    # Convert rows to list for sorting
    row_list = list(rows)
    
    # Primary sort
    row_list.sort(key=lambda r: _get_sort_value(r, sort_key, sort_dir), reverse=(sort_dir == SORT_DESC))
    
    # Tie-breaker: friendly_name (casefolded), then entity_id
    def tie_breaker(row: LowBatteryRow | UnavailableRow) -> tuple:
        return (
            (row.friendly_name or "").casefold(),
            row.entity_id.casefold(),
        )
    
    row_list.sort(key=tie_breaker)
    
    # Re-apply primary sort after tie-breaker
    row_list.sort(key=lambda r: _get_sort_value(r, sort_key, sort_dir), reverse=(sort_dir == SORT_DESC))
    
    return row_list


@dataclass
class PaginatedResult:
    """Result of a paginated query."""
    rows: list[LowBatteryRow | UnavailableRow]
    total_count: int
    next_offset: int | None
    end: bool
    dataset_version: int


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
    
    def increment_version(self, tab: TabType, event: dict | None = None) -> None:
        """Increment dataset version for the given tab."""
        if tab == "low_battery":
            self.low_battery.version += 1
        else:
            self.unavailable.version += 1
        
        # Notify subscribers of the change
        if event:
            self.notify_subscribers(event)
    
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
    
    def get_paginated(
        self,
        tab: TabType,
        sort_by: SortKey = SORT_KEY_FRIENDLY_NAME,
        sort_dir: SortDir = SORT_ASC,
        offset: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
        client_version: int | None = None,
    ) -> PaginatedResult:
        """
        Get a paginated and sorted list of rows.
        
        Args:
            tab: The tab to query (low_battery or unavailable)
            sort_by: Sort key (friendly_name, area, battery_level, entity_id)
            sort_dir: Sort direction (asc or desc)
            offset: Starting offset for pagination
            page_size: Number of rows per page
            client_version: Client's version for invalidation detection
            
        Returns:
            PaginatedResult with rows, counts, and pagination info
        """
        # Check version for invalidation
        current_version = self.get_version(tab)
        invalidated = client_version is not None and client_version != current_version
        
        # Get all rows
        rows_dict = self.get_rows(tab)
        rows_list = list(rows_dict.values())
        
        # Sort the rows
        sorted_rows = _sort_rows(rows_list, sort_by, sort_dir)
        
        # Calculate pagination
        total_count = len(sorted_rows)
        end_offset = offset + page_size
        paginated_rows = sorted_rows[offset:end_offset]
        
        # Determine if there's a next page
        has_next = end_offset < total_count
        next_offset = end_offset if has_next else None
        
        return PaginatedResult(
            rows=paginated_rows,
            total_count=total_count,
            next_offset=next_offset,
            end=not has_next,
            dataset_version=current_version,
        )
    
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
