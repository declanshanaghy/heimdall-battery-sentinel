"""Tests for event subscription functionality."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from custom_components.heimdall_battery_sentinel import (
    _process_state_change,
    _update_low_battery_store,
    _update_unavailable_store,
)
from custom_components.heimdall_battery_sentinel.store import Store
from custom_components.heimdall_battery_sentinel.registry import RegistryCache
from custom_components.heimdall_battery_sentinel.const import TAB_LOW_BATTERY, TAB_UNAVAILABLE


class MockState:
    """Mock state object."""
    def __init__(self, entity_id: str, state: str, attributes: dict = None):
        self.entity_id = entity_id
        self.state = state
        self.attributes = attributes or {}


class MockHass:
    """Mock HomeAssistant object."""
    def __init__(self):
        self.data = {}


class TestProcessStateChange:
    """Tests for _process_state_change function."""

    def test_process_battery_state_change_low_battery(self):
        """Test processing a low battery state change."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        new_state = MockState(
            "sensor.battery_1",
            "10",
            {"device_class": "battery", "unit_of_measurement": "%", "friendly_name": "Battery 1"}
        )
        
        _process_state_change(
            hass, store, registry_cache,
            "sensor.battery_1", None, new_state
        )
        
        # Should be added to low battery
        assert store.get_count(TAB_LOW_BATTERY) == 1
        row = store.get_rows(TAB_LOW_BATTERY)["sensor.battery_1"]
        assert row.battery_numeric == 10.0

    def test_process_battery_state_change_normal_battery(self):
        """Test processing a normal battery state change."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        new_state = MockState(
            "sensor.battery_1",
            "80",
            {"device_class": "battery", "unit_of_measurement": "%", "friendly_name": "Battery 1"}
        )
        
        _process_state_change(
            hass, store, registry_cache,
            "sensor.battery_1", None, new_state
        )
        
        # Should NOT be added to low battery
        assert store.get_count(TAB_LOW_BATTERY) == 0

    def test_process_battery_state_change_non_battery(self):
        """Test processing a non-battery entity."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        new_state = MockState(
            "switch.light",
            "on",
            {"friendly_name": "Light"}
        )
        
        _process_state_change(
            hass, store, registry_cache,
            "switch.light", None, new_state
        )
        
        # Should NOT be added to low battery
        assert store.get_count(TAB_LOW_BATTERY) == 0

    def test_process_unavailable_state(self):
        """Test processing an unavailable entity."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        new_state = MockState(
            "sensor.unknown",
            "unavailable",
            {"friendly_name": "Unknown Sensor"}
        )
        
        _process_state_change(
            hass, store, registry_cache,
            "sensor.unknown", None, new_state
        )
        
        # Should be added to unavailable
        assert store.get_count(TAB_UNAVAILABLE) == 1

    def test_process_available_from_unavailable(self):
        """Test entity becoming available from unavailable."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        # First, add as unavailable
        old_unavailable = MockState(
            "sensor.unknown",
            "unavailable",
            {"friendly_name": "Unknown Sensor"}
        )
        _process_state_change(hass, store, registry_cache, "sensor.unknown", None, old_unavailable)
        assert store.get_count(TAB_UNAVAILABLE) == 1
        
        # Now becomes available
        new_available = MockState(
            "sensor.unknown",
            "25",
            {"friendly_name": "Unknown Sensor"}
        )
        _process_state_change(hass, store, registry_cache, "sensor.unknown", old_unavailable, new_available)
        
        # Should be removed from unavailable
        assert store.get_count(TAB_UNAVAILABLE) == 0

    def test_process_battery_removal(self):
        """Test entity being removed."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        # First, add as low battery
        old_state = MockState(
            "sensor.battery_1",
            "10",
            {"device_class": "battery", "unit_of_measurement": "%", "friendly_name": "Battery 1"}
        )
        _process_state_change(hass, store, registry_cache, "sensor.battery_1", None, old_state)
        assert store.get_count(TAB_LOW_BATTERY) == 1
        
        # Now gets removed (new_state = None)
        _process_state_change(hass, store, registry_cache, "sensor.battery_1", old_state, None)
        
        # Should be removed
        assert store.get_count(TAB_LOW_BATTERY) == 0


class TestTextualBattery:
    """Tests for textual battery handling."""

    def test_process_textual_low_battery(self):
        """Test processing textual 'low' battery."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        new_state = MockState(
            "sensor.battery_text",
            "low",
            {"device_class": "battery", "friendly_name": "Text Battery"}
        )
        
        _process_state_change(
            hass, store, registry_cache,
            "sensor.battery_text", None, new_state
        )
        
        assert store.get_count(TAB_LOW_BATTERY) == 1
        row = store.get_rows(TAB_LOW_BATTERY)["sensor.battery_text"]
        assert row.battery_display == "low"
        # Textual 'low' gets numeric=0 for sorting and severity=RED
        assert row.battery_numeric == 0
        assert row.severity is not None

    def test_process_textual_medium_battery_not_included(self):
        """Test that 'medium' battery is not included in low battery."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        new_state = MockState(
            "sensor.battery_text",
            "medium",
            {"device_class": "battery", "friendly_name": "Text Battery"}
        )
        
        _process_state_change(
            hass, store, registry_cache,
            "sensor.battery_text", None, new_state
        )
        
        assert store.get_count(TAB_LOW_BATTERY) == 0


class TestMetadataInRows:
    """Tests for metadata in row models."""

    def test_low_battery_row_includes_metadata(self):
        """Test that LowBatteryRow includes manufacturer, model, and area."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        # Set up device, entity and area in registry
        class MockDevice:
            def __init__(self, id, manufacturer, model, area_id):
                self.id = id
                self.manufacturer = manufacturer
                self.model = model
                self.area_id = area_id
        
        class MockEntity:
            def __init__(self, entity_id, device_id, area_id, name, original_name):
                self.entity_id = entity_id
                self.device_id = device_id
                self.area_id = area_id
                self.name = name
                self.original_name = original_name
        
        class MockArea:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        registry_cache.update_devices([
            MockDevice("device_1", "Samsung", "Galaxy S21", "area_1"),
        ])
        registry_cache.update_entities([
            MockEntity("sensor.battery_1", "device_1", None, "Battery 1", None),
        ])
        registry_cache.update_areas([
            MockArea("area_1", "Living Room"),
        ])
        
        # Process a low battery state
        new_state = MockState(
            "sensor.battery_1",
            "10",
            {"device_class": "battery", "unit_of_measurement": "%", "friendly_name": "Battery 1"}
        )
        
        _process_state_change(
            hass, store, registry_cache,
            "sensor.battery_1", None, new_state
        )
        
        # Verify metadata is included in the row
        assert store.get_count(TAB_LOW_BATTERY) == 1
        row = store.get_rows(TAB_LOW_BATTERY)["sensor.battery_1"]
        assert row.manufacturer == "Samsung"
        assert row.model == "Galaxy S21"
        assert row.area == "Living Room"

    def test_unavailable_row_includes_metadata(self):
        """Test that UnavailableRow includes manufacturer, model, and area."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        # Set up device, entity and area in registry
        class MockDevice:
            def __init__(self, id, manufacturer, model, area_id):
                self.id = id
                self.manufacturer = manufacturer
                self.model = model
                self.area_id = area_id
        
        class MockEntity:
            def __init__(self, entity_id, device_id, area_id, name, original_name):
                self.entity_id = entity_id
                self.device_id = device_id
                self.area_id = area_id
                self.name = name
                self.original_name = original_name
        
        class MockArea:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        registry_cache.update_devices([
            MockDevice("device_2", "Apple", "iPhone 14", "area_2"),
        ])
        registry_cache.update_entities([
            MockEntity("sensor.unavailable_1", "device_2", None, "Unavailable Sensor", None),
        ])
        registry_cache.update_areas([
            MockArea("area_2", "Kitchen"),
        ])
        
        # Process an unavailable state
        new_state = MockState(
            "sensor.unavailable_1",
            "unavailable",
            {"friendly_name": "Unavailable Sensor"}
        )
        
        _process_state_change(
            hass, store, registry_cache,
            "sensor.unavailable_1", None, new_state
        )
        
        # Verify metadata is included in the row
        assert store.get_count(TAB_UNAVAILABLE) == 1
        row = store.get_rows(TAB_UNAVAILABLE)["sensor.unavailable_1"]
        assert row.manufacturer == "Apple"
        assert row.model == "iPhone 14"
        assert row.area == "Kitchen"

    def test_metadata_resolves_to_none_for_missing_info(self):
        """Test metadata resolves to None when no device/area info."""
        store = Store()
        registry_cache = RegistryCache()
        hass = MockHass()
        
        # No devices or areas in registry
        new_state = MockState(
            "sensor.unknown_battery",
            "10",
            {"device_class": "battery", "unit_of_measurement": "%", "friendly_name": "Unknown Battery"}
        )
        
        _process_state_change(
            hass, store, registry_cache,
            "sensor.unknown_battery", None, new_state
        )
        
        # Verify metadata is None
        row = store.get_rows(TAB_LOW_BATTERY)["sensor.unknown_battery"]
        assert row.manufacturer is None
        assert row.model is None
        assert row.area is None
    """Tests for store notifications."""

    def test_store_notifies_on_change(self):
        """Test that store notifies subscribers on changes."""
        store = Store()
        notified_events = []
        
        def callback(event):
            notified_events.append(event)
        
        store.subscribe(callback)
        
        # Trigger a change
        from custom_components.heimdall_battery_sentinel.models import LowBatteryRow
        from datetime import datetime
        
        row = LowBatteryRow(
            entity_id="sensor.test",
            friendly_name="Test",
            manufacturer=None,
            model=None,
            area=None,
            battery_display="10%",
            battery_numeric=10.0,
            severity=None,
            updated_at=datetime.now()
        )
        store.upsert_row(TAB_LOW_BATTERY, row)
        store.increment_version(TAB_LOW_BATTERY)
        store.notify_subscribers({
            "type": "upsert",
            "tab": TAB_LOW_BATTERY,
            "row": row,
        })
        
        assert len(notified_events) == 1
        assert notified_events[0]["type"] == "upsert"
        assert notified_events[0]["tab"] == TAB_LOW_BATTERY

    def test_store_unsubscribe(self):
        """Test unsubscribing from store."""
        store = Store()
        notified_events = []
        
        def callback(event):
            notified_events.append(event)
        
        sub_id = store.subscribe(callback)
        store.unsubscribe(sub_id)
        
        # Trigger a change
        from custom_components.heimdall_battery_sentinel.models import LowBatteryRow
        from datetime import datetime
        
        row = LowBatteryRow(
            entity_id="sensor.test",
            friendly_name="Test",
            manufacturer=None,
            model=None,
            area=None,
            battery_display="10%",
            battery_numeric=10.0,
            severity=None,
            updated_at=datetime.now()
        )
        store.upsert_row(TAB_LOW_BATTERY, row)
        store.increment_version(TAB_LOW_BATTERY)
        
        # Should not notify unsubscribed callback
        assert len(notified_events) == 0
