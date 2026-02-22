"""Registry helpers for Heimdall Battery Sentinel."""

from typing import TypedDict


class DeviceInfo(TypedDict, total=False):
    """Device information from registry."""
    manufacturer: str | None
    model: str | None
    area_id: str | None
    area_name: str | None


class EntityInfo(TypedDict, total=False):
    """Entity information from registry."""
    device_id: str | None
    area_id: str | None
    name: str | None
    original_name: str | None


class RegistryCache:
    """In-memory cache for registry data."""
    
    def __init__(self):
        self._devices: dict[str, DeviceInfo] = {}
        self._entities: dict[str, EntityInfo] = {}
        self._areas: dict[str, str] = {}  # area_id -> area_name
    
    def update_devices(self, devices: list) -> None:
        """Update device registry cache."""
        self._devices.clear()
        for device in devices:
            device_id = device.id
            self._devices[device_id] = {
                "manufacturer": device.manufacturer,
                "model": device.model,
                "area_id": device.area_id,
            }
    
    def update_entities(self, entities: list) -> None:
        """Update entity registry cache."""
        self._entities.clear()
        for entity in entities:
            entity_id = entity.entity_id
            self._entities[entity_id] = {
                "device_id": entity.device_id,
                "area_id": entity.area_id,
                "name": entity.name,
                "original_name": entity.original_name,
            }
    
    def update_areas(self, areas: list) -> None:
        """Update area registry cache."""
        self._areas.clear()
        for area in areas:
            self._areas[area.id] = area.name
    
    def get_device_info(self, device_id: str | None) -> DeviceInfo | None:
        """Get device info by device ID."""
        if device_id is None:
            return None
        return self._devices.get(device_id)
    
    def get_entity_info(self, entity_id: str) -> EntityInfo | None:
        """Get entity info by entity ID."""
        return self._entities.get(entity_id)
    
    def get_area_name(self, area_id: str | None) -> str | None:
        """Get area name by area ID."""
        if area_id is None:
            return None
        return self._areas.get(area_id)
    
    def resolve_metadata(self, entity_id: str) -> dict:
        """Resolve complete metadata for an entity."""
        entity_info = self.get_entity_info(entity_id)
        
        manufacturer = None
        model = None
        area = None
        
        if entity_info:
            device_id = entity_info.get("device_id")
            if device_id:
                device_info = self.get_device_info(device_id)
                if device_info:
                    manufacturer = device_info.get("manufacturer")
                    model = device_info.get("model")
                    area = self.get_area_name(device_info.get("area_id"))
            
            if area is None and entity_info.get("area_id"):
                area = self.get_area_name(entity_info.get("area_id"))
        
        return {
            "manufacturer": manufacturer,
            "model": model,
            "area": area,
        }
    
    def clear(self) -> None:
        """Clear all caches."""
        self._devices.clear()
        self._entities.clear()
        self._areas.clear()


# Global registry cache instance
_registry_cache = RegistryCache()


def get_registry_cache() -> RegistryCache:
    """Get the global registry cache instance."""
    return _registry_cache
