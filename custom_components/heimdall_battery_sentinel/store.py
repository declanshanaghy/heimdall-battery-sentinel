"""In-memory data store for heimdall_battery_sentinel datasets."""
from __future__ import annotations

import logging
from typing import Callable, Optional

from .const import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_THRESHOLD,
    SORT_DIR_ASC,
    SORT_FIELD_BATTERY_LEVEL,
    SORT_FIELD_FRIENDLY_NAME,
    TAB_LOW_BATTERY,
    TAB_UNAVAILABLE,
    VALID_TABS,
)
from .models import (
    LowBatteryRow,
    UnavailableRow,
    sort_low_battery_rows,
    sort_unavailable_rows,
)

_LOGGER = logging.getLogger(__name__)


class HeimdallStore:
    """Manages in-memory datasets for low-battery and unavailable entities.

    Maintains:
    - Dataset versioning for cache invalidation (per ADR-008).
    - Subscriber list for push websocket updates.
    - Sorted/paged access to rows.
    """

    def __init__(self, threshold: int = DEFAULT_THRESHOLD) -> None:
        """Initialize the store.

        Args:
            threshold: Initial battery threshold percentage.
        """
        self._threshold = threshold
        self._low_battery_version: int = 0
        self._unavailable_version: int = 0
        self._low_battery: dict[str, LowBatteryRow] = {}
        self._unavailable: dict[str, UnavailableRow] = {}
        self._subscribers: list[Callable] = []

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def threshold(self) -> int:
        """Return current battery threshold."""
        return self._threshold

    @property
    def low_battery_version(self) -> int:
        """Return current low-battery dataset version."""
        return self._low_battery_version

    @property
    def unavailable_version(self) -> int:
        """Return current unavailable dataset version."""
        return self._unavailable_version

    @property
    def low_battery_count(self) -> int:
        """Return count of low-battery entities."""
        return len(self._low_battery)

    @property
    def unavailable_count(self) -> int:
        """Return count of unavailable entities."""
        return len(self._unavailable)

    # ── Threshold management ───────────────────────────────────────────────────

    def set_threshold(self, threshold: int) -> None:
        """Update the battery threshold and invalidate datasets.

        Args:
            threshold: New battery threshold (5–100, step 5).
        """
        if threshold != self._threshold:
            self._threshold = threshold
            self._low_battery_version += 1
            _LOGGER.debug("Threshold updated to %d; low_battery_version=%d", threshold, self._low_battery_version)
            self._notify_subscribers({"type": "invalidated", "tab": TAB_LOW_BATTERY, "dataset_version": self._low_battery_version})
            self._notify_subscribers({
                "type": "summary",
                "low_battery_count": self.low_battery_count,
                "unavailable_count": self.unavailable_count,
                "threshold": self._threshold,
            })

    # ── Low-battery dataset ────────────────────────────────────────────────────

    def upsert_low_battery(self, row: LowBatteryRow) -> None:
        """Insert or update a low-battery row.

        Args:
            row: The LowBatteryRow to upsert.
        """
        self._low_battery[row.entity_id] = row
        _LOGGER.debug("Upserted low_battery row: %s", row.entity_id)
        self._notify_subscribers({
            "type": "upsert",
            "tab": TAB_LOW_BATTERY,
            "row": row.as_dict(),
            "dataset_version": self._low_battery_version,
        })

    def remove_low_battery(self, entity_id: str) -> bool:
        """Remove a low-battery row by entity_id.

        Args:
            entity_id: Entity ID to remove.

        Returns:
            True if removed, False if not found.
        """
        if entity_id in self._low_battery:
            del self._low_battery[entity_id]
            _LOGGER.debug("Removed low_battery row: %s", entity_id)
            self._notify_subscribers({
                "type": "remove",
                "tab": TAB_LOW_BATTERY,
                "entity_id": entity_id,
                "dataset_version": self._low_battery_version,
            })
            return True
        return False

    def bulk_set_low_battery(self, rows: list[LowBatteryRow]) -> None:
        """Replace the entire low-battery dataset.

        Increments the dataset version and notifies subscribers.

        Args:
            rows: Complete list of LowBatteryRow objects.
        """
        self._low_battery = {row.entity_id: row for row in rows}
        self._low_battery_version += 1
        _LOGGER.debug("Bulk set %d low_battery rows; version=%d", len(rows), self._low_battery_version)
        self._notify_subscribers({
            "type": "invalidated",
            "tab": TAB_LOW_BATTERY,
            "dataset_version": self._low_battery_version,
        })
        self._notify_subscribers({
            "type": "summary",
            "low_battery_count": self.low_battery_count,
            "unavailable_count": self.unavailable_count,
            "threshold": self._threshold,
        })

    # ── Unavailable dataset ────────────────────────────────────────────────────

    def upsert_unavailable(self, row: UnavailableRow) -> None:
        """Insert or update an unavailable row.

        Args:
            row: The UnavailableRow to upsert.
        """
        self._unavailable[row.entity_id] = row
        _LOGGER.debug("Upserted unavailable row: %s", row.entity_id)
        self._notify_subscribers({
            "type": "upsert",
            "tab": TAB_UNAVAILABLE,
            "row": row.as_dict(),
            "dataset_version": self._unavailable_version,
        })

    def remove_unavailable(self, entity_id: str) -> bool:
        """Remove an unavailable row by entity_id.

        Args:
            entity_id: Entity ID to remove.

        Returns:
            True if removed, False if not found.
        """
        if entity_id in self._unavailable:
            del self._unavailable[entity_id]
            _LOGGER.debug("Removed unavailable row: %s", entity_id)
            self._notify_subscribers({
                "type": "remove",
                "tab": TAB_UNAVAILABLE,
                "entity_id": entity_id,
                "dataset_version": self._unavailable_version,
            })
            return True
        return False

    def bulk_set_unavailable(self, rows: list[UnavailableRow]) -> None:
        """Replace the entire unavailable dataset.

        Increments the dataset version and notifies subscribers.

        Args:
            rows: Complete list of UnavailableRow objects.
        """
        self._unavailable = {row.entity_id: row for row in rows}
        self._unavailable_version += 1
        _LOGGER.debug("Bulk set %d unavailable rows; version=%d", len(rows), self._unavailable_version)
        self._notify_subscribers({
            "type": "invalidated",
            "tab": TAB_UNAVAILABLE,
            "dataset_version": self._unavailable_version,
        })
        self._notify_subscribers({
            "type": "summary",
            "low_battery_count": self.low_battery_count,
            "unavailable_count": self.unavailable_count,
            "threshold": self._threshold,
        })

    # ── Query interface ────────────────────────────────────────────────────────

    def get_summary(self) -> dict:
        """Return a summary of current counts and configuration.

        Returns:
            Dict with low_battery_count, unavailable_count, threshold,
            low_battery_version, unavailable_version.
        """
        return {
            "low_battery_count": self.low_battery_count,
            "unavailable_count": self.unavailable_count,
            "threshold": self._threshold,
            "low_battery_version": self._low_battery_version,
            "unavailable_version": self._unavailable_version,
        }

    def get_page(
        self,
        tab: str,
        sort_by: str,
        sort_dir: str,
        offset: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
        client_version: Optional[int] = None,
    ) -> dict:
        """Return a paginated page of rows for a given tab.

        Per ADR-008, if client_version is stale the response will include
        ``invalidated=True`` to prompt client to refresh from page 0.

        Args:
            tab: "low_battery" or "unavailable".
            sort_by: Column to sort by.
            sort_dir: "asc" or "desc".
            offset: Zero-based row offset.
            page_size: Maximum rows to return (default 100).
            client_version: Dataset version the client last saw, or None.

        Returns:
            Dict with rows, next_offset, end, dataset_version, invalidated.
        """
        if tab not in VALID_TABS:
            raise ValueError(f"Invalid tab: {tab!r}. Must be one of {VALID_TABS}")

        if tab == TAB_LOW_BATTERY:
            current_version = self._low_battery_version
            all_rows = sort_low_battery_rows(
                list(self._low_battery.values()), sort_by, sort_dir
            )
        else:
            current_version = self._unavailable_version
            all_rows = sort_unavailable_rows(
                list(self._unavailable.values()), sort_by, sort_dir
            )

        invalidated = client_version is not None and client_version != current_version
        if invalidated and offset != 0:
            # Client should restart from page 0
            return {
                "rows": [],
                "next_offset": None,
                "end": False,
                "dataset_version": current_version,
                "invalidated": True,
            }

        page = all_rows[offset: offset + page_size]
        end = (offset + len(page)) >= len(all_rows)
        next_offset = offset + len(page) if not end else None

        rows_dicts = [r.as_dict() for r in page]

        return {
            "rows": rows_dicts,
            "next_offset": next_offset,
            "end": end,
            "dataset_version": current_version,
            "invalidated": invalidated,
        }

    # ── Subscriber management ──────────────────────────────────────────────────

    def subscribe(self, callback: Callable) -> Callable:
        """Register a subscriber callback.

        Args:
            callback: Callable that receives a dict event message.

        Returns:
            An unsubscribe callable.
        """
        self._subscribers.append(callback)

        def unsubscribe():
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass

        return unsubscribe

    def _notify_subscribers(self, message: dict) -> None:
        """Notify all subscribers with a message.

        Args:
            message: Event dict to broadcast.
        """
        for callback in list(self._subscribers):
            try:
                callback(message)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Error notifying subscriber with message %r", message)
