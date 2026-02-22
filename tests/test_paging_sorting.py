"""Tests for server-side paging and sorting in store."""

import pytest
from datetime import datetime

from custom_components.heimdall_battery_sentinel.const import (
    DEFAULT_PAGE_SIZE,
    SORT_ASC,
    SORT_DESC,
    SORT_KEY_AREA,
    SORT_KEY_BATTERY_LEVEL,
    SORT_KEY_ENTITY_ID,
    SORT_KEY_FRIENDLY_NAME,
    SORT_KEY_UPDATED_AT,
)
from custom_components.heimdall_battery_sentinel.models import LowBatteryRow, Severity, UnavailableRow
from custom_components.heimdall_battery_sentinel.store import (
    PaginatedResult,
    _sort_rows,
    get_store,
)


class TestSortRows:
    """Tests for the _sort_rows function."""

    def test_sort_by_friendly_name_asc(self):
        """Test sorting by friendly name ascending."""
        rows = [
            LowBatteryRow(
                entity_id="sensor.zigbee_battery",
                friendly_name="Zigbee Battery",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display="15%",
                battery_numeric=15.0,
                severity=Severity.ORANGE,
                updated_at=datetime.now(),
            ),
            LowBatteryRow(
                entity_id="sensor.abc_battery",
                friendly_name="ABC Battery",
                manufacturer="Unknown",
                model=None,
                area="Bedroom",
                battery_display="10%",
                battery_numeric=10.0,
                severity=Severity.RED,
                updated_at=datetime.now(),
            ),
        ]
        
        sorted_rows = _sort_rows(rows, SORT_KEY_FRIENDLY_NAME, SORT_ASC)
        
        assert sorted_rows[0].entity_id == "sensor.abc_battery"
        assert sorted_rows[1].entity_id == "sensor.zigbee_battery"

    def test_sort_by_friendly_name_desc(self):
        """Test sorting by friendly name descending."""
        rows = [
            LowBatteryRow(
                entity_id="sensor.abc_battery",
                friendly_name="ABC Battery",
                manufacturer="Unknown",
                model=None,
                area="Bedroom",
                battery_display="10%",
                battery_numeric=10.0,
                severity=Severity.RED,
                updated_at=datetime.now(),
            ),
            LowBatteryRow(
                entity_id="sensor.zigbee_battery",
                friendly_name="Zigbee Battery",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display="15%",
                battery_numeric=15.0,
                severity=Severity.ORANGE,
                updated_at=datetime.now(),
            ),
        ]
        
        sorted_rows = _sort_rows(rows, SORT_KEY_FRIENDLY_NAME, SORT_DESC)
        
        assert sorted_rows[0].entity_id == "sensor.zigbee_battery"
        assert sorted_rows[1].entity_id == "sensor.abc_battery"

    def test_sort_by_battery_level_asc(self):
        """Test sorting by battery level ascending."""
        rows = [
            LowBatteryRow(
                entity_id="sensor.high_battery",
                friendly_name="High Battery",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display="20%",
                battery_numeric=20.0,
                severity=Severity.YELLOW,
                updated_at=datetime.now(),
            ),
            LowBatteryRow(
                entity_id="sensor.low_battery",
                friendly_name="Low Battery",
                manufacturer="Unknown",
                model=None,
                area="Bedroom",
                battery_display="5%",
                battery_numeric=5.0,
                severity=Severity.RED,
                updated_at=datetime.now(),
            ),
        ]
        
        sorted_rows = _sort_rows(rows, SORT_KEY_BATTERY_LEVEL, SORT_ASC)
        
        assert sorted_rows[0].entity_id == "sensor.low_battery"
        assert sorted_rows[1].entity_id == "sensor.high_battery"

    def test_sort_by_battery_level_desc(self):
        """Test sorting by battery level descending."""
        rows = [
            LowBatteryRow(
                entity_id="sensor.low_battery",
                friendly_name="Low Battery",
                manufacturer="Unknown",
                model=None,
                area="Bedroom",
                battery_display="5%",
                battery_numeric=5.0,
                severity=Severity.RED,
                updated_at=datetime.now(),
            ),
            LowBatteryRow(
                entity_id="sensor.high_battery",
                friendly_name="High Battery",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display="20%",
                battery_numeric=20.0,
                severity=Severity.YELLOW,
                updated_at=datetime.now(),
            ),
        ]
        
        sorted_rows = _sort_rows(rows, SORT_KEY_BATTERY_LEVEL, SORT_DESC)
        
        assert sorted_rows[0].entity_id == "sensor.high_battery"
        assert sorted_rows[1].entity_id == "sensor.low_battery"

    def test_sort_by_entity_id_asc(self):
        """Test sorting by entity_id ascending."""
        rows = [
            LowBatteryRow(
                entity_id="sensor.zigbee_battery",
                friendly_name="Zigbee",
                manufacturer="Unknown",
                model=None,
                area=None,
                battery_display="15%",
                battery_numeric=15.0,
                severity=Severity.ORANGE,
                updated_at=datetime.now(),
            ),
            LowBatteryRow(
                entity_id="sensor.abc_battery",
                friendly_name="ABC",
                manufacturer="Unknown",
                model=None,
                area=None,
                battery_display="10%",
                battery_numeric=10.0,
                severity=Severity.RED,
                updated_at=datetime.now(),
            ),
        ]
        
        sorted_rows = _sort_rows(rows, SORT_KEY_ENTITY_ID, SORT_ASC)
        
        assert sorted_rows[0].entity_id == "sensor.abc_battery"
        assert sorted_rows[1].entity_id == "sensor.zigbee_battery"

    def test_tie_breaker_friendly_name(self):
        """Test that friendly_name is used as tie-breaker."""
        rows = [
            # Same friendly name
            LowBatteryRow(
                entity_id="sensor.battery_b",
                friendly_name="Battery",
                manufacturer="Unknown",
                model=None,
                area=None,
                battery_display="15%",
                battery_numeric=15.0,
                severity=Severity.ORANGE,
                updated_at=datetime.now(),
            ),
            LowBatteryRow(
                entity_id="sensor.battery_a",
                friendly_name="Battery",
                manufacturer="Unknown",
                model=None,
                area=None,
                battery_display="10%",
                battery_numeric=10.0,
                severity=Severity.RED,
                updated_at=datetime.now(),
            ),
        ]
        
        sorted_rows = _sort_rows(rows, SORT_KEY_BATTERY_LEVEL, SORT_ASC)
        
        # Entity_id should be the final tie-breaker
        assert sorted_rows[0].entity_id == "sensor.battery_a"
        assert sorted_rows[1].entity_id == "sensor.battery_b"

    def test_sort_by_updated_at_asc(self):
        """Test sorting by updated_at ascending."""
        rows = [
            LowBatteryRow(
                entity_id="sensor.new",
                friendly_name="New Sensor",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display="15%",
                battery_numeric=15.0,
                severity=Severity.ORANGE,
                updated_at=datetime(2026, 2, 21, 12, 0, 0),
            ),
            LowBatteryRow(
                entity_id="sensor.old",
                friendly_name="Old Sensor",
                manufacturer="Unknown",
                model=None,
                area="Bedroom",
                battery_display="10%",
                battery_numeric=10.0,
                severity=Severity.RED,
                updated_at=datetime(2026, 2, 20, 12, 0, 0),
            ),
        ]
        
        sorted_rows = _sort_rows(rows, SORT_KEY_UPDATED_AT, SORT_ASC)
        
        # Oldest should be first (ascending)
        assert sorted_rows[0].entity_id == "sensor.old"
        assert sorted_rows[1].entity_id == "sensor.new"

    def test_sort_by_updated_at_desc(self):
        """Test sorting by updated_at descending."""
        rows = [
            LowBatteryRow(
                entity_id="sensor.old",
                friendly_name="Old Sensor",
                manufacturer="Unknown",
                model=None,
                area="Bedroom",
                battery_display="10%",
                battery_numeric=10.0,
                severity=Severity.RED,
                updated_at=datetime(2026, 2, 20, 12, 0, 0),
            ),
            LowBatteryRow(
                entity_id="sensor.new",
                friendly_name="New Sensor",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display="15%",
                battery_numeric=15.0,
                severity=Severity.ORANGE,
                updated_at=datetime(2026, 2, 21, 12, 0, 0),
            ),
        ]
        
        sorted_rows = _sort_rows(rows, SORT_KEY_UPDATED_AT, SORT_DESC)
        
        # Newest should be first (descending)
        assert sorted_rows[0].entity_id == "sensor.new"
        assert sorted_rows[1].entity_id == "sensor.old"

    def test_sort_by_updated_at_none_handling(self):
        """Test that None updated_at values sort last."""
        rows = [
            LowBatteryRow(
                entity_id="sensor.with_date",
                friendly_name="With Date",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display="15%",
                battery_numeric=15.0,
                severity=Severity.ORANGE,
                updated_at=datetime(2026, 2, 21, 12, 0, 0),
            ),
            LowBatteryRow(
                entity_id="sensor.without_date",
                friendly_name="Without Date",
                manufacturer="Unknown",
                model=None,
                area="Bedroom",
                battery_display="10%",
                battery_numeric=10.0,
                severity=Severity.RED,
                updated_at=None,
            ),
        ]
        
        sorted_rows = _sort_rows(rows, SORT_KEY_UPDATED_AT, SORT_ASC)
        
        # Row with date should be first, None should be last
        assert sorted_rows[0].entity_id == "sensor.with_date"
        assert sorted_rows[1].entity_id == "sensor.without_date"


class TestGetPaginated:
    """Tests for the get_paginated method."""

    def setup_method(self):
        """Set up test store."""
        self.store = get_store()
        # Clear the store
        self.store.low_battery.rows_by_id.clear()
        self.store.unavailable.rows_by_id.clear()

    def test_pagination_first_page(self):
        """Test getting first page of results."""
        # Add 150 rows
        for i in range(150):
            row = LowBatteryRow(
                entity_id=f"sensor.battery_{i:03d}",
                friendly_name=f"Battery {i:03d}",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display=f"{i}%",
                battery_numeric=float(i),
                severity=Severity.YELLOW if i > 10 else Severity.ORANGE,
                updated_at=datetime.now(),
            )
            self.store.upsert_row("low_battery", row)
        
        result = self.store.get_paginated(
            "low_battery",
            sort_by=SORT_KEY_FRIENDLY_NAME,
            sort_dir=SORT_ASC,
            offset=0,
            page_size=100,
        )
        
        assert len(result.rows) == 100
        assert result.total_count == 150
        assert result.next_offset == 100
        assert result.end is False

    def test_pagination_second_page(self):
        """Test getting second page of results."""
        # Add 150 rows
        for i in range(150):
            row = LowBatteryRow(
                entity_id=f"sensor.battery_{i:03d}",
                friendly_name=f"Battery {i:03d}",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display=f"{i}%",
                battery_numeric=float(i),
                severity=Severity.YELLOW if i > 10 else Severity.ORANGE,
                updated_at=datetime.now(),
            )
            self.store.upsert_row("low_battery", row)
        
        result = self.store.get_paginated(
            "low_battery",
            sort_by=SORT_KEY_FRIENDLY_NAME,
            sort_dir=SORT_ASC,
            offset=100,
            page_size=100,
        )
        
        assert len(result.rows) == 50
        assert result.total_count == 150
        assert result.next_offset is None
        assert result.end is True

    def test_pagination_exact_page(self):
        """Test getting exact number of rows that fit in a page."""
        # Add 100 rows
        for i in range(100):
            row = LowBatteryRow(
                entity_id=f"sensor.battery_{i:03d}",
                friendly_name=f"Battery {i:03d}",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display=f"{i}%",
                battery_numeric=float(i),
                severity=Severity.YELLOW,
                updated_at=datetime.now(),
            )
            self.store.upsert_row("low_battery", row)
        
        result = self.store.get_paginated(
            "low_battery",
            offset=0,
            page_size=100,
        )
        
        assert len(result.rows) == 100
        assert result.total_count == 100
        assert result.next_offset is None
        assert result.end is True

    def test_pagination_empty(self):
        """Test pagination with no rows."""
        result = self.store.get_paginated("low_battery")
        
        assert len(result.rows) == 0
        assert result.total_count == 0
        assert result.next_offset is None
        assert result.end is True

    def test_pagination_with_sorting(self):
        """Test pagination with sorting."""
        # Add rows with different battery levels
        self.store.upsert_row(
            "low_battery",
            LowBatteryRow(
                entity_id="sensor.high",
                friendly_name="High",
                manufacturer="Unknown",
                model=None,
                area="Living Room",
                battery_display="80%",
                battery_numeric=80.0,
                severity=Severity.YELLOW,
                updated_at=datetime.now(),
            ),
        )
        self.store.upsert_row(
            "low_battery",
            LowBatteryRow(
                entity_id="sensor.low",
                friendly_name="Low",
                manufacturer="Unknown",
                model=None,
                area="Bedroom",
                battery_display="10%",
                battery_numeric=10.0,
                severity=Severity.RED,
                updated_at=datetime.now(),
            ),
        )
        
        # Sort by battery level ascending
        result = self.store.get_paginated(
            "low_battery",
            sort_by=SORT_KEY_BATTERY_LEVEL,
            sort_dir=SORT_ASC,
        )
        
        assert result.rows[0].entity_id == "sensor.low"
        assert result.rows[1].entity_id == "sensor.high"

    def test_pagination_version_tracking(self):
        """Test that pagination returns dataset version."""
        row = LowBatteryRow(
            entity_id="sensor.test",
            friendly_name="Test",
            manufacturer="Unknown",
            model=None,
            area="Living Room",
            battery_display="15%",
            battery_numeric=15.0,
            severity=Severity.ORANGE,
            updated_at=datetime.now(),
        )
        self.store.upsert_row("low_battery", row)
        # Version is incremented after upsert in real usage
        self.store.increment_version("low_battery", {"type": "upsert", "tab": "low_battery", "row": row})
        
        result = self.store.get_paginated("low_battery")
        
        assert result.dataset_version == 1

    def test_pagination_invalidated_flag(self):
        """Test invalidation flag when client version differs."""
        row = LowBatteryRow(
            entity_id="sensor.test",
            friendly_name="Test",
            manufacturer="Unknown",
            model=None,
            area="Living Room",
            battery_display="15%",
            battery_numeric=15.0,
            severity=Severity.ORANGE,
            updated_at=datetime.now(),
        )
        self.store.upsert_row("low_battery", row)
        current_version = self.store.get_version("low_battery") + 1
        self.store.increment_version("low_battery", {"type": "upsert", "tab": "low_battery", "row": row})
        
        # Client has old version (0)
        result = self.store.get_paginated("low_battery", client_version=0)
        
        # Version should be current_version
        assert result.dataset_version == current_version

    def test_default_page_size(self):
        """Test that default page size is used."""
        assert DEFAULT_PAGE_SIZE == 100
