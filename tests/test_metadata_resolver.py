"""Unit tests for registry.py — metadata enrichment (ADR-006, Story 3-2)."""
import pytest
from unittest.mock import MagicMock, patch

from custom_components.heimdall_battery_sentinel.registry import (
    MetadataResolver,
    get_metadata_fn,
)


class TestMetadataResolver:
    """Test the MetadataResolver class (ADR-006, Story 3-2 AC1-AC5).

    Per ADR-006: Metadata is resolved from HA registries (entity, device, area)
    and cached per entity_id. Cache is invalidated on registry updates.
    """

    def test_resolver_initialization(self):
        """Test MetadataResolver initializes with empty cache."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        assert resolver._entity_meta_cache == {}
        assert resolver._hass is hass

    def test_invalidate_cache_clears_entries(self):
        """Test invalidate_cache() clears all cached entries."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        # Manually add cache entries
        resolver._entity_meta_cache["test.entity"] = ("mfg", "model", "area", "dev_id")
        assert len(resolver._entity_meta_cache) == 1
        
        resolver.invalidate_cache()
        assert len(resolver._entity_meta_cache) == 0

    def test_resolve_returns_cached_value_on_second_call(self):
        """Test resolve() returns cached value without calling registries again."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        # Mock registries
        ent_reg = MagicMock()
        ent_entry = MagicMock()
        ent_entry.device_id = None
        ent_entry.area_id = None
        ent_reg.async_get.return_value = ent_entry
        hass.helpers.entity_registry.async_get.return_value = ent_reg
        
        # First call should hit registries
        result1 = resolver.resolve("sensor.test")
        assert hass.helpers.entity_registry.async_get.call_count == 1
        
        # Second call should use cache (no additional registry calls)
        result2 = resolver.resolve("sensor.test")
        assert hass.helpers.entity_registry.async_get.call_count == 1  # Still 1
        assert result1 == result2

    def test_resolve_with_entity_not_found(self):
        """Test resolve() returns all None when entity not in registry."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        ent_reg = MagicMock()
        ent_reg.async_get.return_value = None  # Entity not found
        hass.helpers.entity_registry.async_get.return_value = ent_reg
        
        result = resolver.resolve("sensor.nonexistent")
        assert result == (None, None, None, None)

    def test_resolve_with_device_metadata_success(self):
        """Test resolve() retrieves manufacturer/model from device registry."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        # Mock entity registry
        ent_reg = MagicMock()
        ent_entry = MagicMock()
        ent_entry.device_id = "device_123"
        ent_entry.area_id = None
        ent_reg.async_get.return_value = ent_entry
        hass.helpers.entity_registry.async_get.return_value = ent_reg
        
        # Mock device registry
        dev_reg = MagicMock()
        dev_entry = MagicMock()
        dev_entry.manufacturer = "Acme Corp"
        dev_entry.model = "BatteryBox 5000"
        dev_entry.area_id = None
        dev_reg.async_get.return_value = dev_entry
        hass.helpers.device_registry.async_get.return_value = dev_reg
        
        # Mock area registry (not used in this case)
        area_reg = MagicMock()
        hass.helpers.area_registry.async_get.return_value = area_reg
        
        manufacturer, model, area, device_id = resolver.resolve("sensor.battery1")
        
        assert manufacturer == "Acme Corp"
        assert model == "BatteryBox 5000"
        assert area is None
        assert device_id == "device_123"

    def test_resolve_with_area_from_device_registry(self):
        """Test resolve() retrieves area from device registry (preferred)."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        # Mock entity registry
        ent_reg = MagicMock()
        ent_entry = MagicMock()
        ent_entry.device_id = "device_456"
        ent_entry.area_id = None  # No area on entity
        ent_reg.async_get.return_value = ent_entry
        hass.helpers.entity_registry.async_get.return_value = ent_reg
        
        # Mock device registry with area
        dev_reg = MagicMock()
        dev_entry = MagicMock()
        dev_entry.manufacturer = "Brand X"
        dev_entry.model = "Model X"
        dev_entry.area_id = "area_123"  # Area on device
        dev_reg.async_get.return_value = dev_entry
        hass.helpers.device_registry.async_get.return_value = dev_reg
        
        # Mock area registry
        area_reg = MagicMock()
        area_entry = MagicMock()
        area_entry.name = "Living Room"
        area_reg.async_get_area.return_value = area_entry
        hass.helpers.area_registry.async_get.return_value = area_reg
        
        manufacturer, model, area, device_id = resolver.resolve("sensor.test")
        
        assert manufacturer == "Brand X"
        assert model == "Model X"
        assert area == "Living Room"
        assert device_id == "device_456"

    def test_resolve_with_area_fallback_to_entity_area(self):
        """Test resolve() falls back to entity area if device area is None (ADR-006)."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        # Mock entity registry with area
        ent_reg = MagicMock()
        ent_entry = MagicMock()
        ent_entry.device_id = "device_789"
        ent_entry.area_id = "area_789"  # Area on entity
        ent_reg.async_get.return_value = ent_entry
        hass.helpers.entity_registry.async_get.return_value = ent_reg
        
        # Mock device registry without area
        dev_reg = MagicMock()
        dev_entry = MagicMock()
        dev_entry.manufacturer = "Brand Y"
        dev_entry.model = "Model Y"
        dev_entry.area_id = None  # No area on device
        dev_reg.async_get.return_value = dev_entry
        hass.helpers.device_registry.async_get.return_value = dev_reg
        
        # Mock area registry
        area_reg = MagicMock()
        area_entry = MagicMock()
        area_entry.name = "Kitchen"
        area_reg.async_get_area.return_value = area_entry
        hass.helpers.area_registry.async_get.return_value = area_reg
        
        manufacturer, model, area, device_id = resolver.resolve("sensor.test")
        
        assert manufacturer == "Brand Y"
        assert model == "Model Y"
        assert area == "Kitchen"  # From entity area
        assert device_id == "device_789"

    def test_resolve_with_missing_manufacturer_model(self):
        """Test resolve() handles missing manufacturer/model as None."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        # Mock entity registry
        ent_reg = MagicMock()
        ent_entry = MagicMock()
        ent_entry.device_id = "device_orphan"
        ent_entry.area_id = None
        ent_reg.async_get.return_value = ent_entry
        hass.helpers.entity_registry.async_get.return_value = ent_reg
        
        # Mock device registry with missing values
        dev_reg = MagicMock()
        dev_entry = MagicMock()
        dev_entry.manufacturer = None
        dev_entry.model = None
        dev_entry.area_id = None
        dev_reg.async_get.return_value = dev_entry
        hass.helpers.device_registry.async_get.return_value = dev_reg
        
        # Mock area registry
        area_reg = MagicMock()
        hass.helpers.area_registry.async_get.return_value = area_reg
        
        manufacturer, model, area, device_id = resolver.resolve("sensor.orphan")
        
        assert manufacturer is None
        assert model is None
        assert area is None
        assert device_id == "device_orphan"

    def test_resolve_with_no_device_id(self):
        """Test resolve() handles entities without device_id."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        # Mock entity registry without device_id
        ent_reg = MagicMock()
        ent_entry = MagicMock()
        ent_entry.device_id = None  # No device
        ent_entry.area_id = "area_999"
        ent_reg.async_get.return_value = ent_entry
        hass.helpers.entity_registry.async_get.return_value = ent_reg
        
        # Mock area registry
        area_reg = MagicMock()
        area_entry = MagicMock()
        area_entry.name = "Basement"
        area_reg.async_get_area.return_value = area_entry
        hass.helpers.area_registry.async_get.return_value = area_reg
        
        manufacturer, model, area, device_id = resolver.resolve("sensor.orphan")
        
        assert manufacturer is None
        assert model is None
        assert area == "Basement"  # From entity area
        assert device_id is None

    def test_resolve_for_all_batch_resolves_multiple_entities(self):
        """Test resolve_for_all() resolves metadata for multiple entities."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        # Mock registries to return different metadata per entity
        ent_reg = MagicMock()
        dev_reg = MagicMock()
        area_reg = MagicMock()
        
        hass.helpers.entity_registry.async_get.return_value = ent_reg
        hass.helpers.device_registry.async_get.return_value = dev_reg
        hass.helpers.area_registry.async_get.return_value = area_reg
        
        # Setup side effects for entity registry
        def ent_get_side_effect(entity_id):
            responses = {
                "sensor.batt1": MagicMock(device_id="dev1", area_id=None),
                "sensor.batt2": MagicMock(device_id="dev2", area_id=None),
            }
            return responses.get(entity_id)
        
        ent_reg.async_get.side_effect = ent_get_side_effect
        
        # Setup side effects for device registry
        def dev_get_side_effect(device_id):
            responses = {
                "dev1": MagicMock(manufacturer="Mfg1", model="Model1", area_id=None),
                "dev2": MagicMock(manufacturer="Mfg2", model="Model2", area_id=None),
            }
            return responses.get(device_id)
        
        dev_reg.async_get.side_effect = dev_get_side_effect
        
        results = resolver.resolve_for_all(["sensor.batt1", "sensor.batt2"])
        
        assert results["sensor.batt1"] == ("Mfg1", "Model1", None, "dev1")
        assert results["sensor.batt2"] == ("Mfg2", "Model2", None, "dev2")

    def test_get_metadata_fn_returns_callable(self):
        """Test get_metadata_fn() returns a callable function."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        metadata_fn = get_metadata_fn(resolver)
        
        assert callable(metadata_fn)

    def test_get_metadata_fn_callable_uses_resolver(self):
        """Test the callable returned by get_metadata_fn() uses resolver.resolve()."""
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        # Mock entity registry
        ent_reg = MagicMock()
        ent_entry = MagicMock()
        ent_entry.device_id = "device_test"
        ent_entry.area_id = None
        ent_reg.async_get.return_value = ent_entry
        hass.helpers.entity_registry.async_get.return_value = ent_reg
        
        # Mock device registry
        dev_reg = MagicMock()
        dev_entry = MagicMock()
        dev_entry.manufacturer = "TestMfg"
        dev_entry.model = "TestModel"
        dev_entry.area_id = None
        dev_reg.async_get.return_value = dev_entry
        hass.helpers.device_registry.async_get.return_value = dev_reg
        
        # Mock area registry
        area_reg = MagicMock()
        hass.helpers.area_registry.async_get.return_value = area_reg
        
        metadata_fn = get_metadata_fn(resolver)
        result = metadata_fn("sensor.test")
        
        assert result == ("TestMfg", "TestModel", None, "device_test")


class TestMetadataResolverCacheInvalidation:
    """Test cache invalidation behavior (Story 3-2, AC4)."""

    def test_cache_invalidation_on_registry_update(self):
        """AC4: Cache is invalidated when registries change.

        Per story 3-2 AC4: Metadata must update in real-time when device/area
        registries change. This test verifies the cache invalidation mechanism.
        """
        hass = MagicMock()
        resolver = MetadataResolver(hass)
        
        # Mock registries
        ent_reg = MagicMock()
        dev_reg = MagicMock()
        area_reg = MagicMock()
        
        hass.helpers.entity_registry.async_get.return_value = ent_reg
        hass.helpers.device_registry.async_get.return_value = dev_reg
        hass.helpers.area_registry.async_get.return_value = area_reg
        
        # Setup initial metadata
        ent_entry = MagicMock()
        ent_entry.device_id = "device_1"
        ent_entry.area_id = None
        ent_reg.async_get.return_value = ent_entry
        
        dev_entry = MagicMock()
        dev_entry.manufacturer = "OldMfg"
        dev_entry.model = "OldModel"
        dev_entry.area_id = None
        dev_reg.async_get.return_value = dev_entry
        
        # First resolve - should hit registries and cache
        result1 = resolver.resolve("sensor.test")
        assert result1[0] == "OldMfg"
        cache_hits = hass.helpers.device_registry.async_get.call_count
        
        # Simulate registry update - update device manufacturer
        dev_entry.manufacturer = "NewMfg"
        
        # Second resolve without invalidation should return cached old value
        result2 = resolver.resolve("sensor.test")
        assert result2[0] == "OldMfg"  # Still cached
        
        # Invalidate cache and resolve again
        resolver.invalidate_cache()
        result3 = resolver.resolve("sensor.test")
        assert result3[0] == "NewMfg"  # Now updated
        
        # Verify registry was called again after invalidation
        assert hass.helpers.device_registry.async_get.call_count > cache_hits
