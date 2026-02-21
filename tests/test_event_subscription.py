"""Tests for event subscription system (story 1-2).

Verifies that:
- Initial datasets are populated from HA state snapshot
- State change events are detected and processed within 5 seconds (design goal)
- Event handlers correctly update datasets incrementally
- Dataset versions increment on changes
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, call
from datetime import datetime, timedelta

from custom_components.heimdall_battery_sentinel.const import (
    DOMAIN,
    DATA_STORE,
    DATA_REGISTRY,
    DEFAULT_THRESHOLD,
    TAB_LOW_BATTERY,
    TAB_UNAVAILABLE,
    SORT_FIELD_FRIENDLY_NAME,
    SORT_DIR_ASC,
)
from custom_components.heimdall_battery_sentinel.store import HeimdallStore
from custom_components.heimdall_battery_sentinel.evaluator import BatteryEvaluator
from custom_components.heimdall_battery_sentinel.models import LowBatteryRow, UnavailableRow
from custom_components.heimdall_battery_sentinel.registry import MetadataResolver


class TestInitialDatasetPopulation:
    """AC: Initial dataset population from HA state snapshot."""

    def test_populate_initial_low_battery_datasets(self, mock_hass, mock_state):
        """Verify initial population includes low battery entities."""
        # Arrange: Create mock HA states
        states = [
            mock_state("sensor.battery_1", "10", {"unit_of_measurement": "%", "device_class": "battery"}),
            mock_state("sensor.battery_2", "50", {"unit_of_measurement": "%", "device_class": "battery"}),
            mock_state("sensor.battery_3", "5", {"unit_of_measurement": "%", "device_class": "battery"}),
        ]
        mock_hass.states.async_all.return_value = states

        # Act: Populate store from mock states
        store = HeimdallStore(threshold=15)
        evaluator = BatteryEvaluator(threshold=15)
        
        # Simulate what _populate_initial_datasets does
        def metadata_fn(entity_id):
            return None, None, None  # No metadata for this test
        
        low_battery_rows, unavailable_rows = evaluator.batch_evaluate(states, metadata_fn)
        store.bulk_set_low_battery(low_battery_rows)
        store.bulk_set_unavailable(unavailable_rows)

        # Assert
        assert store.low_battery_count == 2  # 10% and 5% are below threshold 15
        assert store.unavailable_count == 0
        
        # Verify both low batteries are in the store
        page = store.get_page(TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC, offset=0, page_size=100)
        entity_ids = [row["entity_id"] for row in page["rows"]]
        assert "sensor.battery_1" in entity_ids
        assert "sensor.battery_3" in entity_ids
        assert "sensor.battery_2" not in entity_ids  # 50% is above threshold

    def test_populate_initial_unavailable_datasets(self, mock_hass, mock_state):
        """Verify initial population includes unavailable entities."""
        # Arrange
        states = [
            mock_state("sensor.temp", "20", {}),
            mock_state("sensor.humidity", "unavailable", {}),
            mock_state("switch.light", "unavailable", {}),
            mock_state("sensor.battery", "on", {}),
        ]
        mock_hass.states.async_all.return_value = states

        # Act
        store = HeimdallStore(threshold=15)
        evaluator = BatteryEvaluator(threshold=15)
        
        def metadata_fn(entity_id):
            return None, None, None
        
        low_battery_rows, unavailable_rows = evaluator.batch_evaluate(states, metadata_fn)
        store.bulk_set_unavailable(unavailable_rows)

        # Assert
        assert store.unavailable_count == 2  # humidity and light are unavailable
        page = store.get_page(TAB_UNAVAILABLE, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC, offset=0, page_size=100)
        entity_ids = [row["entity_id"] for row in page["rows"]]
        assert "sensor.humidity" in entity_ids
        assert "switch.light" in entity_ids
        assert "sensor.temp" not in entity_ids

    def test_initial_population_empty_ha(self, mock_hass):
        """Verify population works when HA has no states."""
        # Arrange
        mock_hass.states.async_all.return_value = []

        # Act
        store = HeimdallStore(threshold=15)
        evaluator = BatteryEvaluator(threshold=15)
        
        def metadata_fn(entity_id):
            return None, None, None
        
        low_battery_rows, unavailable_rows = evaluator.batch_evaluate([], metadata_fn)
        store.bulk_set_low_battery(low_battery_rows)
        store.bulk_set_unavailable(unavailable_rows)

        # Assert
        assert store.low_battery_count == 0
        assert store.unavailable_count == 0


class TestStateChangeEventHandling:
    """AC: State change events are detected and datasets updated incrementally."""

    def test_state_change_creates_low_battery_entry(self, mock_state):
        """Verify state change creating a low battery entry."""
        # Arrange
        store = HeimdallStore(threshold=15)
        evaluator = BatteryEvaluator(threshold=15)
        
        def metadata_fn(entity_id):
            return "Manufacturer", "Model", "Living Room"
        
        # Act: New battery state below threshold
        new_state = mock_state("sensor.battery", "10", {
            "unit_of_measurement": "%",
            "device_class": "battery",
            "friendly_name": "Device Battery"
        })
        
        lb_row = evaluator.evaluate_low_battery(new_state, "Manufacturer", "Model", "Living Room")
        if lb_row:
            store.upsert_low_battery(lb_row)

        # Assert
        assert store.low_battery_count == 1
        page = store.get_page(TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC, offset=0, page_size=100)
        assert len(page["rows"]) == 1
        assert page["rows"][0]["entity_id"] == "sensor.battery"
        assert page["rows"][0]["battery_numeric"] == 10.0

    def test_state_change_removes_low_battery_entry(self, mock_state):
        """Verify state change removing a low battery entry."""
        # Arrange
        store = HeimdallStore(threshold=15)
        evaluator = BatteryEvaluator(threshold=15)
        
        # Pre-populate with a low battery
        row = LowBatteryRow(
            entity_id="sensor.battery",
            friendly_name="Device",
            battery_display="10%",
            battery_numeric=10.0,
            area="Living Room"
        )
        store.upsert_low_battery(row)
        assert store.low_battery_count == 1

        # Act: Battery now high
        new_state = mock_state("sensor.battery", "80", {
            "unit_of_measurement": "%",
            "device_class": "battery"
        })
        
        lb_row = evaluator.evaluate_low_battery(new_state, "Manufacturer", "Model", "Living Room")
        if lb_row is None:  # Not low anymore
            store.remove_low_battery("sensor.battery")

        # Assert
        assert store.low_battery_count == 0

    def test_state_change_creates_unavailable_entry(self, mock_state):
        """Verify state change creating an unavailable entry."""
        # Arrange
        store = HeimdallStore(threshold=15)
        evaluator = BatteryEvaluator(threshold=15)

        # Act: Entity becomes unavailable
        new_state = mock_state("sensor.temp", "unavailable", {
            "friendly_name": "Temperature Sensor"
        })
        
        un_row = evaluator.evaluate_unavailable(new_state, "Mfg", "Model", "Kitchen")
        if un_row:
            store.upsert_unavailable(un_row)

        # Assert
        assert store.unavailable_count == 1
        page = store.get_page(TAB_UNAVAILABLE, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC, offset=0, page_size=100)
        assert len(page["rows"]) == 1
        assert page["rows"][0]["entity_id"] == "sensor.temp"

    def test_state_change_removes_unavailable_entry(self, mock_state):
        """Verify state change removing an unavailable entry."""
        # Arrange
        store = HeimdallStore(threshold=15)
        
        # Pre-populate with an unavailable
        row = UnavailableRow(
            entity_id="sensor.temp",
            friendly_name="Temperature",
            area="Kitchen"
        )
        store.upsert_unavailable(row)
        assert store.unavailable_count == 1

        # Act: Sensor comes back online
        new_state = mock_state("sensor.temp", "20.5", {})
        evaluator = BatteryEvaluator(threshold=15)
        
        un_row = evaluator.evaluate_unavailable(new_state, None, None, None)
        if un_row is None:  # No longer unavailable
            store.remove_unavailable("sensor.temp")

        # Assert
        assert store.unavailable_count == 0


class TestDatasetVersioning:
    """AC: Dataset version increments on changes."""

    def test_low_battery_version_increments(self):
        """Verify low battery dataset version increments on bulk_set."""
        # Arrange
        store = HeimdallStore(threshold=15)
        initial_version = store.low_battery_version

        # Act
        row = LowBatteryRow(
            entity_id="sensor.battery",
            friendly_name="Device",
            battery_display="10%",
            battery_numeric=10.0,
            area=None
        )
        store.bulk_set_low_battery([row])

        # Assert
        assert store.low_battery_version > initial_version
        assert store.low_battery_version == initial_version + 1

    def test_unavailable_version_increments(self):
        """Verify unavailable dataset version increments on bulk_set."""
        # Arrange
        store = HeimdallStore(threshold=15)
        initial_version = store.unavailable_version

        # Act
        row = UnavailableRow(
            entity_id="sensor.temp",
            friendly_name="Temp",
            area=None
        )
        store.bulk_set_unavailable([row])

        # Assert
        assert store.unavailable_version > initial_version
        assert store.unavailable_version == initial_version + 1

    def test_version_increments_on_threshold_change(self):
        """Verify versions increment on threshold change."""
        # Arrange
        store = HeimdallStore(threshold=15)
        version_before = store.low_battery_version

        # Act: Update threshold
        store.set_threshold(20)

        # Assert
        assert store.low_battery_version > version_before
        assert store.threshold == 20


class TestEventDetectionSpeed:
    """AC: Changes detected within 5 seconds (design goal test)."""

    def test_state_change_detection_is_synchronous(self, mock_state):
        """Verify state changes are processed synchronously (subsecond)."""
        # Arrange
        store = HeimdallStore(threshold=15)
        evaluator = BatteryEvaluator(threshold=15)
        
        new_state = mock_state("sensor.battery", "10", {
            "unit_of_measurement": "%",
            "device_class": "battery",
            "friendly_name": "Battery"
        })

        # Act: Record timestamps
        start_time = datetime.now()
        lb_row = evaluator.evaluate_low_battery(new_state, None, None, None)
        if lb_row:
            store.upsert_low_battery(lb_row)
        end_time = datetime.now()

        # Assert: Should complete in milliseconds, well under 5 seconds
        elapsed = (end_time - start_time).total_seconds()
        assert elapsed < 5.0  # Design goal: 5 seconds max
        assert elapsed < 0.1  # Should be much faster in practice


class TestDatasetInvalidation:
    """AC: Dataset invalidation on configuration changes."""

    def test_bulk_set_updates_all_rows(self):
        """Verify bulk_set replaces entire dataset."""
        # Arrange
        store = HeimdallStore(threshold=15)
        
        # Pre-populate
        row1 = LowBatteryRow(
            entity_id="sensor.battery_1",
            friendly_name="Battery 1",
            battery_display="10%",
            battery_numeric=10.0,
            area=None
        )
        store.upsert_low_battery(row1)
        assert store.low_battery_count == 1

        # Act: Bulk replace with new rows
        row2 = LowBatteryRow(
            entity_id="sensor.battery_2",
            friendly_name="Battery 2",
            battery_display="5%",
            battery_numeric=5.0,
            area=None
        )
        store.bulk_set_low_battery([row2])

        # Assert
        assert store.low_battery_count == 1
        page = store.get_page(TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC, offset=0, page_size=100)
        assert page["rows"][0]["entity_id"] == "sensor.battery_2"
        assert page["rows"][0]["entity_id"] != "sensor.battery_1"
