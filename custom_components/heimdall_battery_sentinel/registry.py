"""Entity registry management and metadata enrichment for heimdall_battery_sentinel."""
from __future__ import annotations

import logging
from typing import Optional, Tuple

_LOGGER = logging.getLogger(__name__)

# Type alias for metadata result
MetaTuple = Tuple[Optional[str], Optional[str], Optional[str]]  # (manufacturer, model, area)


class MetadataResolver:
    """Resolves manufacturer, model, and area metadata from HA registries.

    Per ADR-006:
    - entity_registry → device_id
    - device_registry → manufacturer, model
    - area_registry → area name (prefer device area, fallback entity area)

    Metadata is cached per entity_id / device_id and invalidated on registry update.
    """

    def __init__(self, hass) -> None:
        """Initialize the resolver with a HA instance.

        Args:
            hass: Home Assistant instance.
        """
        self._hass = hass
        self._entity_meta_cache: dict[str, MetaTuple] = {}

    def invalidate_cache(self) -> None:
        """Clear the metadata cache (call on registry update events)."""
        _LOGGER.debug("MetadataResolver: clearing metadata cache (%d entries)", len(self._entity_meta_cache))
        self._entity_meta_cache.clear()

    def resolve(self, entity_id: str) -> MetaTuple:
        """Resolve metadata for an entity.

        Args:
            entity_id: The entity ID to look up.

        Returns:
            Tuple of (manufacturer, model, area). Each may be None if unavailable.
        """
        if entity_id in self._entity_meta_cache:
            return self._entity_meta_cache[entity_id]

        meta = self._resolve_uncached(entity_id)
        self._entity_meta_cache[entity_id] = meta
        return meta

    def _resolve_uncached(self, entity_id: str) -> MetaTuple:
        """Resolve metadata without consulting the cache.

        Args:
            entity_id: The entity ID to look up.

        Returns:
            Tuple of (manufacturer, model, area).
        """
        try:
            ent_reg = self._hass.helpers.entity_registry.async_get(self._hass)
        except AttributeError:
            # HA >= 2023.x changed registry access
            try:
                from homeassistant.helpers.entity_registry import async_get as er_async_get
                ent_reg = er_async_get(self._hass)
            except Exception:
                _LOGGER.debug("Could not access entity registry for %s", entity_id)
                return (None, None, None)

        entry = ent_reg.async_get(entity_id)
        if entry is None:
            _LOGGER.debug("Entity %s not found in entity registry", entity_id)
            return (None, None, None)

        device_id = entry.device_id
        entity_area_id = entry.area_id

        manufacturer: Optional[str] = None
        model: Optional[str] = None
        device_area_id: Optional[str] = None

        if device_id:
            try:
                dev_reg = self._hass.helpers.device_registry.async_get(self._hass)
            except AttributeError:
                try:
                    from homeassistant.helpers.device_registry import async_get as dr_async_get
                    dev_reg = dr_async_get(self._hass)
                except Exception:
                    dev_reg = None

            if dev_reg:
                dev_entry = dev_reg.async_get(device_id)
                if dev_entry:
                    manufacturer = dev_entry.manufacturer
                    model = dev_entry.model
                    device_area_id = dev_entry.area_id

        # Prefer device area, fall back to entity area
        area_id = device_area_id or entity_area_id
        area_name: Optional[str] = None

        if area_id:
            try:
                area_reg = self._hass.helpers.area_registry.async_get(self._hass)
            except AttributeError:
                try:
                    from homeassistant.helpers.area_registry import async_get as ar_async_get
                    area_reg = ar_async_get(self._hass)
                except Exception:
                    area_reg = None

            if area_reg:
                area_entry = area_reg.async_get_area(area_id)
                if area_entry:
                    area_name = area_entry.name

        return (manufacturer or None, model or None, area_name)

    def resolve_for_all(self, entity_ids: list[str]) -> dict[str, MetaTuple]:
        """Resolve metadata for a list of entity IDs.

        Args:
            entity_ids: List of entity IDs.

        Returns:
            Dict mapping entity_id → (manufacturer, model, area).
        """
        return {eid: self.resolve(eid) for eid in entity_ids}


def get_metadata_fn(resolver: MetadataResolver):
    """Return a metadata lookup function suitable for BatteryEvaluator.batch_evaluate.

    Args:
        resolver: A MetadataResolver instance.

    Returns:
        Callable that takes entity_id and returns (manufacturer, model, area).
    """
    def metadata_fn(entity_id: str) -> MetaTuple:
        return resolver.resolve(entity_id)
    return metadata_fn
