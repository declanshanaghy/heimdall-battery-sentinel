"""Tests for metadata enrichment functionality."""

import pytest
from datetime import datetime

from custom_components.heimdall_battery_sentinel.registry import (
    RegistryCache,
    DeviceInfo,
    EntityInfo,
)


class TestRegistryCache:
    """Tests for the RegistryCache class."""

    def test_update_devices(self):
        """Test device registry cache update."""
        # Create mock device objects
        class MockDevice:
            def __init__(self, id, manufacturer, model, area_id):
                self.id = id
                self.manufacturer = manufacturer
                self.model = model
                self.area_id = area_id

        cache = RegistryCache()
        
        devices = [
            MockDevice("device_1", "Samsung", "Galaxy S21", "area_1"),
            MockDevice("device_2", "Apple", "iPhone 14", None),
            MockDevice("device_3", None, None, "area_2"),
        ]
        
        cache.update_devices(devices)
        
        assert cache.get_device_info("device_1") == {
            "manufacturer": "Samsung",
            "model": "Galaxy S21",
            "area_id": "area_1",
        }
        assert cache.get_device_info("device_2") == {
            "manufacturer": "Apple",
            "model": "iPhone 14",
            "area_id": None,
        }
        assert cache.get_device_info("device_3") == {
            "manufacturer": None,
            "model": None,
            "area_id": "area_2",
        }
        assert cache.get_device_info("nonexistent") is None

    def test_update_entities(self):
        """Test entity registry cache update."""
        class MockEntity:
            def __init__(self, entity_id, device_id, area_id, name, original_name):
                self.entity_id = entity_id
                self.device_id = device_id
                self.area_id = area_id
                self.name = name
                self.original_name = original_name

        cache = RegistryCache()
        
        entities = [
            MockEntity("light.living_room", "device_1", None, "Living Room", None),
            MockEntity("sensor.outdoor_temp", None, "area_2", "Outdoor Temp", "Outdoor Temperature"),
        ]
        
        cache.update_entities(entities)
        
        assert cache.get_entity_info("light.living_room") == {
            "device_id": "device_1",
            "area_id": None,
            "name": "Living Room",
            "original_name": None,
        }
        assert cache.get_entity_info("sensor.outdoor_temp") == {
            "device_id": None,
            "area_id": "area_2",
            "name": "Outdoor Temp",
            "original_name": "Outdoor Temperature",
        }
        assert cache.get_entity_info("nonexistent") is None

    def test_update_areas(self):
        """Test area registry cache update."""
        class MockArea:
            def __init__(self, id, name):
                self.id = id
                self.name = name

        cache = RegistryCache()
        
        areas = [
            MockArea("area_1", "Living Room"),
            MockArea("area_2", "Kitchen"),
            MockArea("area_3", "Bedroom"),
        ]
        
        cache.update_areas(areas)
        
        assert cache.get_area_name("area_1") == "Living Room"
        assert cache.get_area_name("area_2") == "Kitchen"
        assert cache.get_area_name("area_3") == "Bedroom"
        assert cache.get_area_name("nonexistent") is None
        assert cache.get_area_name(None) is None

    def test_resolve_metadata_with_device_info(self):
        """Test metadata resolution when device info is available."""
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

        cache = RegistryCache()
        cache.update_devices([
            MockDevice("device_1", "Samsung", "Galaxy S21", "area_1"),
        ])
        cache.update_entities([
            MockEntity("sensor.battery_1", "device_1", None, "Battery", None),
        ])
        cache.update_areas([
            MockArea("area_1", "Living Room"),
        ])
        
        metadata = cache.resolve_metadata("sensor.battery_1")
        
        assert metadata == {
            "manufacturer": "Samsung",
            "model": "Galaxy S21",
            "area": "Living Room",  # Device area takes priority
        }

    def test_resolve_metadata_fallback_to_entity_area(self):
        """Test metadata resolution falls back to entity area when device has no area."""
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

        cache = RegistryCache()
        cache.update_devices([
            MockDevice("device_1", "Apple", "iPhone 14", None),  # No device area
        ])
        cache.update_entities([
            MockEntity("sensor.battery_1", "device_1", "area_2", "Battery", None),
        ])
        cache.update_areas([
            MockArea("area_2", "Kitchen"),
        ])
        
        metadata = cache.resolve_metadata("sensor.battery_1")
        
        assert metadata == {
            "manufacturer": "Apple",
            "model": "iPhone 14",
            "area": "Kitchen",  # Falls back to entity area
        }

    def test_resolve_metadata_no_device(self):
        """Test metadata resolution when entity has no device."""
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

        cache = RegistryCache()
        cache.update_entities([
            MockEntity("sensor.battery_1", None, "area_2", "Battery", None),
        ])
        cache.update_areas([
            MockArea("area_2", "Kitchen"),
        ])
        
        metadata = cache.resolve_metadata("sensor.battery_1")
        
        assert metadata == {
            "manufacturer": None,
            "model": None,
            "area": "Kitchen",
        }

    def test_resolve_metadata_no_metadata_at_all(self):
        """Test metadata resolution when entity has no metadata at all."""
        cache = RegistryCache()
        
        metadata = cache.resolve_metadata("sensor.battery_1")
        
        assert metadata == {
            "manufacturer": None,
            "model": None,
            "area": None,
        }

    def test_resolve_metadata_manufacturer_model_only(self):
        """Test metadata resolution when only manufacturer/model available."""
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

        cache = RegistryCache()
        cache.update_devices([
            MockDevice("device_1", "Samsung", "Galaxy S21", None),
        ])
        cache.update_entities([
            MockEntity("sensor.battery_1", "device_1", None, "Battery", None),
        ])
        
        metadata = cache.resolve_metadata("sensor.battery_1")
        
        assert metadata == {
            "manufacturer": "Samsung",
            "model": "Galaxy S21",
            "area": None,
        }

    def test_clear_cache(self):
        """Test clearing the cache."""
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

        cache = RegistryCache()
        cache.update_devices([MockDevice("device_1", "Samsung", "Galaxy S21", None)])
        cache.update_entities([MockEntity("sensor.battery_1", "device_1", None, "Battery", None)])
        cache.update_areas([MockArea("area_1", "Living Room")])
        
        cache.clear()
        
        assert cache.get_device_info("device_1") is None
        assert cache.get_entity_info("sensor.battery_1") is None
        assert cache.get_area_name("area_1") is None
