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


class TestStoreNotifications:
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
