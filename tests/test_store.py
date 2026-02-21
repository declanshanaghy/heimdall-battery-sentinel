"""Unit tests for store.py — in-memory dataset management."""
import pytest

from custom_components.heimdall_battery_sentinel.store import HeimdallStore
from custom_components.heimdall_battery_sentinel.models import LowBatteryRow, UnavailableRow
from custom_components.heimdall_battery_sentinel.const import (
    DEFAULT_THRESHOLD,
    TAB_LOW_BATTERY,
    TAB_UNAVAILABLE,
    SORT_DIR_ASC,
    SORT_DIR_DESC,
    SORT_FIELD_FRIENDLY_NAME,
    SORT_FIELD_BATTERY_LEVEL,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lb(entity_id, friendly_name="Entity", battery_numeric=10.0, battery_display="10%", area=None):
    """Create a test LowBatteryRow.
    
    Args:
        entity_id: Entity ID (required).
        friendly_name: Display name (default: "Entity").
        battery_numeric: Numeric battery level (default: 10.0%).
        battery_display: Display string (default: "10%").
        area: Area name or None (default: None).
    
    Returns:
        LowBatteryRow instance for testing.
    """
    return LowBatteryRow(
        entity_id=entity_id,
        friendly_name=friendly_name,
        battery_display=battery_display,
        battery_numeric=battery_numeric,
        area=area,
    )


def _uv(entity_id, friendly_name="Entity"):
    """Create a test UnavailableRow.
    
    Args:
        entity_id: Entity ID (required).
        friendly_name: Display name (default: "Entity").
    
    Returns:
        UnavailableRow instance for testing.
    """
    return UnavailableRow(entity_id=entity_id, friendly_name=friendly_name)


# ── HeimdallStore initialization ──────────────────────────────────────────────

class TestHeimdallStoreInit:
    def test_default_threshold(self):
        store = HeimdallStore()
        assert store.threshold == DEFAULT_THRESHOLD

    def test_custom_threshold(self):
        store = HeimdallStore(threshold=20)
        assert store.threshold == 20

    def test_initial_counts_are_zero(self):
        store = HeimdallStore()
        assert store.low_battery_count == 0
        assert store.unavailable_count == 0

    def test_initial_versions_are_zero(self):
        store = HeimdallStore()
        assert store.low_battery_version == 0
        assert store.unavailable_version == 0


# ── Low-battery CRUD ──────────────────────────────────────────────────────────

class TestLowBatteryCRUD:
    def test_upsert_adds_row(self):
        store = HeimdallStore()
        store.upsert_low_battery(_lb("sensor.a"))
        assert store.low_battery_count == 1

    def test_upsert_updates_existing(self):
        store = HeimdallStore()
        store.upsert_low_battery(_lb("sensor.a", battery_numeric=10.0))
        store.upsert_low_battery(_lb("sensor.a", battery_numeric=5.0))
        assert store.low_battery_count == 1

    def test_remove_existing_returns_true(self):
        store = HeimdallStore()
        store.upsert_low_battery(_lb("sensor.a"))
        result = store.remove_low_battery("sensor.a")
        assert result is True
        assert store.low_battery_count == 0

    def test_remove_nonexistent_returns_false(self):
        store = HeimdallStore()
        result = store.remove_low_battery("sensor.nonexistent")
        assert result is False

    def test_bulk_set_replaces_all(self):
        store = HeimdallStore()
        store.upsert_low_battery(_lb("sensor.old"))
        store.bulk_set_low_battery([_lb("sensor.a"), _lb("sensor.b")])
        assert store.low_battery_count == 2

    def test_bulk_set_increments_version(self):
        store = HeimdallStore()
        v0 = store.low_battery_version
        store.bulk_set_low_battery([_lb("sensor.a")])
        assert store.low_battery_version == v0 + 1


# ── Unavailable CRUD ──────────────────────────────────────────────────────────

class TestUnavailableCRUD:
    def test_upsert_adds_row(self):
        store = HeimdallStore()
        store.upsert_unavailable(_uv("light.lamp"))
        assert store.unavailable_count == 1

    def test_remove_existing_returns_true(self):
        store = HeimdallStore()
        store.upsert_unavailable(_uv("light.lamp"))
        result = store.remove_unavailable("light.lamp")
        assert result is True
        assert store.unavailable_count == 0

    def test_bulk_set_increments_version(self):
        store = HeimdallStore()
        v0 = store.unavailable_version
        store.bulk_set_unavailable([_uv("light.a")])
        assert store.unavailable_version == v0 + 1


# ── Threshold management ──────────────────────────────────────────────────────

class TestThreshold:
    def test_set_threshold_changes_value(self):
        store = HeimdallStore(threshold=15)
        store.set_threshold(20)
        assert store.threshold == 20

    def test_set_threshold_increments_low_battery_version(self):
        store = HeimdallStore(threshold=15)
        v0 = store.low_battery_version
        store.set_threshold(20)
        assert store.low_battery_version == v0 + 1

    def test_set_same_threshold_no_version_change(self):
        store = HeimdallStore(threshold=15)
        v0 = store.low_battery_version
        store.set_threshold(15)  # no-op
        assert store.low_battery_version == v0


# ── get_summary ───────────────────────────────────────────────────────────────

class TestGetSummary:
    def test_summary_has_required_keys(self):
        store = HeimdallStore(threshold=15)
        summary = store.get_summary()
        assert "low_battery_count" in summary
        assert "unavailable_count" in summary
        assert "threshold" in summary
        assert "low_battery_version" in summary
        assert "unavailable_version" in summary

    def test_summary_reflects_actual_counts(self):
        store = HeimdallStore(threshold=15)
        store.upsert_low_battery(_lb("sensor.a"))
        store.upsert_unavailable(_uv("light.b"))
        summary = store.get_summary()
        assert summary["low_battery_count"] == 1
        assert summary["unavailable_count"] == 1
        assert summary["threshold"] == 15


# ── get_page ──────────────────────────────────────────────────────────────────

class TestGetPage:
    def _store_with_lb_rows(self, n):
        store = HeimdallStore()
        for i in range(n):
            store.upsert_low_battery(_lb(f"sensor.{i:03d}", friendly_name=f"Entity {i:03d}", battery_numeric=float(i + 1)))
        return store

    def test_get_page_returns_dict(self):
        store = HeimdallStore()
        result = store.get_page(TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC)
        assert isinstance(result, dict)
        assert "rows" in result
        assert "end" in result
        assert "dataset_version" in result
        assert "invalidated" in result

    def test_get_page_empty_store(self):
        store = HeimdallStore()
        result = store.get_page(TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC)
        assert result["rows"] == []
        assert result["end"] is True

    def test_get_page_returns_rows(self):
        store = self._store_with_lb_rows(5)
        result = store.get_page(TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC)
        assert len(result["rows"]) == 5
        assert result["end"] is True

    def test_get_page_pagination(self):
        store = self._store_with_lb_rows(10)
        page1 = store.get_page(TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC, offset=0, page_size=5)
        assert len(page1["rows"]) == 5
        assert page1["end"] is False
        assert page1["next_offset"] == 5

        page2 = store.get_page(TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC, offset=5, page_size=5)
        assert len(page2["rows"]) == 5
        assert page2["end"] is True

    def test_get_page_no_duplicate_rows_across_pages(self):
        store = self._store_with_lb_rows(10)
        page1 = store.get_page(TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC, offset=0, page_size=5)
        page2 = store.get_page(TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC, offset=5, page_size=5)
        ids_p1 = {r["entity_id"] for r in page1["rows"]}
        ids_p2 = {r["entity_id"] for r in page2["rows"]}
        assert ids_p1.isdisjoint(ids_p2)

    def test_get_page_invalid_tab_raises(self):
        store = HeimdallStore()
        with pytest.raises(ValueError):
            store.get_page("invalid_tab", SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC)

    def test_get_page_stale_version_mid_page_triggers_invalidation(self):
        """If client sends stale version with offset > 0, response has invalidated=True."""
        store = HeimdallStore()
        store.bulk_set_low_battery([_lb(f"sensor.{i}") for i in range(5)])
        version = store.low_battery_version
        # Simulate dataset change
        store.bulk_set_low_battery([_lb(f"sensor.{i}") for i in range(6)])
        new_version = store.low_battery_version
        assert new_version != version

        # Client requests with stale version at offset > 0
        result = store.get_page(
            TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC,
            offset=2, client_version=version
        )
        assert result["invalidated"] is True
        assert result["rows"] == []

    def test_get_page_correct_version_no_invalidation(self):
        store = HeimdallStore()
        store.bulk_set_low_battery([_lb("sensor.a")])
        version = store.low_battery_version
        result = store.get_page(
            TAB_LOW_BATTERY, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC,
            client_version=version
        )
        assert result["invalidated"] is False

    def test_unavailable_page(self):
        store = HeimdallStore()
        store.upsert_unavailable(_uv("light.a", "Alpha"))
        store.upsert_unavailable(_uv("light.b", "Beta"))
        result = store.get_page(TAB_UNAVAILABLE, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC)
        assert len(result["rows"]) == 2
        assert result["rows"][0]["friendly_name"] == "Alpha"


# ── Subscriber management ─────────────────────────────────────────────────────

class TestSubscribers:
    def test_subscriber_called_on_upsert(self):
        store = HeimdallStore()
        events = []
        store.subscribe(lambda e: events.append(e))
        store.upsert_low_battery(_lb("sensor.a"))
        assert any(e.get("type") == "upsert" for e in events)

    def test_subscriber_called_on_remove(self):
        store = HeimdallStore()
        store.upsert_low_battery(_lb("sensor.a"))
        events = []
        store.subscribe(lambda e: events.append(e))
        store.remove_low_battery("sensor.a")
        assert any(e.get("type") == "remove" for e in events)

    def test_subscriber_called_on_bulk_set(self):
        store = HeimdallStore()
        events = []
        store.subscribe(lambda e: events.append(e))
        store.bulk_set_low_battery([_lb("sensor.a")])
        assert any(e.get("type") == "invalidated" for e in events)

    def test_unsubscribe_stops_notifications(self):
        store = HeimdallStore()
        events = []
        unsubscribe = store.subscribe(lambda e: events.append(e))
        unsubscribe()
        store.upsert_low_battery(_lb("sensor.a"))
        assert len(events) == 0

    def test_multiple_subscribers(self):
        store = HeimdallStore()
        calls_a = []
        calls_b = []
        store.subscribe(lambda e: calls_a.append(e))
        store.subscribe(lambda e: calls_b.append(e))
        store.upsert_low_battery(_lb("sensor.a"))
        assert len(calls_a) > 0
        assert len(calls_b) > 0

    def test_subscriber_exception_does_not_crash_store(self):
        store = HeimdallStore()
        def bad_subscriber(e):
            raise RuntimeError("boom")
        store.subscribe(bad_subscriber)
        # Should not raise
        store.upsert_low_battery(_lb("sensor.a"))
        assert store.low_battery_count == 1


# ── AC4: Device-level filtering (one battery per device) ──────────────────────

class TestAC4DeviceFiltering:
    """AC4 requires: For devices with multiple battery entities, 
    select the first by entity_id ascending.
    
    These tests verify AC4 is enforced during incremental updates 
    (upsert_low_battery operations after initial batch_evaluate).
    """

    def test_upsert_two_batteries_same_device_keeps_first_by_entity_id(self):
        """AC4: When upserting two batteries for the same device, keep only first by entity_id."""
        store = HeimdallStore()
        device_id = "device_phone"
        
        # Add first battery (lower entity_id)
        row1 = _lb("sensor.phone_battery_level", battery_numeric=8.0)
        row1.device_id = device_id
        store.upsert_low_battery(row1)
        
        assert store.low_battery_count == 1
        assert store._low_battery["sensor.phone_battery_level"] is not None
        
        # Add second battery for same device (higher entity_id, also low)
        row2 = _lb("sensor.phone_main_battery", battery_numeric=5.0)
        row2.device_id = device_id
        store.upsert_low_battery(row2)
        
        # AC4: Should still have only 1 battery (the first by entity_id)
        assert store.low_battery_count == 1
        assert "sensor.phone_battery_level" in store._low_battery
        assert "sensor.phone_main_battery" not in store._low_battery

    def test_upsert_lower_entity_id_replaces_higher_entity_id(self):
        """AC4: If a lower entity_id battery is upser later, it replaces the higher one."""
        store = HeimdallStore()
        device_id = "device_watch"
        
        # Add battery with higher entity_id first
        row_high = _lb("sensor.watch_z_battery", battery_numeric=5.0)
        row_high.device_id = device_id
        store.upsert_low_battery(row_high)
        assert store.low_battery_count == 1
        
        # Add battery with lower entity_id for same device
        row_low = _lb("sensor.watch_a_battery", battery_numeric=8.0)
        row_low.device_id = device_id
        store.upsert_low_battery(row_low)
        
        # AC4: Should now have the lower entity_id battery
        assert store.low_battery_count == 1
        assert "sensor.watch_a_battery" in store._low_battery
        assert "sensor.watch_z_battery" not in store._low_battery

    def test_upsert_same_battery_updates_in_place(self):
        """AC4: Upserting the same battery entity updates it in place."""
        store = HeimdallStore()
        device_id = "device_tag"
        
        # Add battery
        row1 = _lb("sensor.tag_battery", battery_numeric=10.0)
        row1.device_id = device_id
        store.upsert_low_battery(row1)
        
        # Update same battery
        row2 = _lb("sensor.tag_battery", battery_numeric=5.0)
        row2.device_id = device_id
        store.upsert_low_battery(row2)
        
        # Should still have 1 battery with updated value
        assert store.low_battery_count == 1
        assert store._low_battery["sensor.tag_battery"].battery_numeric == 5.0

    def test_upsert_multiple_devices_each_keeps_first_by_entity_id(self):
        """AC4: Multiple devices each with multiple batteries → keep first per device."""
        store = HeimdallStore()
        
        # Device A: add two batteries
        row_a1 = _lb("sensor.device_a_bat1", battery_numeric=5.0)
        row_a1.device_id = "device_a"
        store.upsert_low_battery(row_a1)
        
        row_a2 = _lb("sensor.device_a_bat2", battery_numeric=8.0)
        row_a2.device_id = "device_a"
        store.upsert_low_battery(row_a2)
        
        # Device B: add two batteries
        row_b1 = _lb("sensor.device_b_bat1", battery_numeric=10.0)
        row_b1.device_id = "device_b"
        store.upsert_low_battery(row_b1)
        
        row_b2 = _lb("sensor.device_b_bat2", battery_numeric=12.0)
        row_b2.device_id = "device_b"
        store.upsert_low_battery(row_b2)
        
        # Should have exactly 2 batteries: one per device, first by entity_id
        assert store.low_battery_count == 2
        entity_ids = set(store._low_battery.keys())
        assert "sensor.device_a_bat1" in entity_ids
        assert "sensor.device_b_bat1" in entity_ids
        assert "sensor.device_a_bat2" not in entity_ids
        assert "sensor.device_b_bat2" not in entity_ids

    def test_upsert_without_device_id_not_filtered(self):
        """AC4: Batteries without device_id are not subject to per-device filtering."""
        store = HeimdallStore()
        
        # Add two batteries without device_id
        row1 = _lb("sensor.battery_a", battery_numeric=8.0)
        # device_id is None by default
        store.upsert_low_battery(row1)
        
        row2 = _lb("sensor.battery_b", battery_numeric=5.0)
        # device_id is None by default
        store.upsert_low_battery(row2)
        
        # Both should be kept (no device_id means no per-device constraint)
        assert store.low_battery_count == 2
        assert "sensor.battery_a" in store._low_battery
        assert "sensor.battery_b" in store._low_battery

    def test_upsert_mixed_with_and_without_device_id(self):
        """AC4: Mix of batteries with and without device_id work correctly."""
        store = HeimdallStore()
        
        # Device with device_id (add two batteries, keep first)
        row1 = _lb("sensor.device_bat_a", battery_numeric=8.0)
        row1.device_id = "device_1"
        store.upsert_low_battery(row1)
        
        row2 = _lb("sensor.device_bat_b", battery_numeric=5.0)
        row2.device_id = "device_1"
        store.upsert_low_battery(row2)
        
        # Standalone battery without device_id
        row3 = _lb("sensor.standalone_bat", battery_numeric=10.0)
        # device_id is None
        store.upsert_low_battery(row3)
        
        # Should have 2: device_bat_a (per device_id) + standalone_bat
        assert store.low_battery_count == 2
        assert "sensor.device_bat_a" in store._low_battery
        assert "sensor.device_bat_b" not in store._low_battery
        assert "sensor.standalone_bat" in store._low_battery

    def test_ac4_incremental_path_batch_then_event(self):
        """AC4: Full incremental update path - batch_evaluate then state_changed event.
        
        Scenario:
        1. Initial batch_evaluate with AC4 filtering (done at startup)
        2. State change event triggers upsert_low_battery for a new battery
        3. Verify AC4 constraint is still enforced
        """
        from custom_components.heimdall_battery_sentinel.evaluator import BatteryEvaluator
        from unittest.mock import MagicMock
        
        store = HeimdallStore(threshold=15)
        evaluator = BatteryEvaluator(threshold=15)
        
        # --- STEP 1: Initial batch_evaluate (simulating startup) ---
        def _state(entity_id, state_val, device_class=None, unit=None):
            s = MagicMock()
            s.entity_id = entity_id
            s.state = state_val
            attrs = {}
            if device_class:
                attrs["device_class"] = device_class
            if unit:
                attrs["unit_of_measurement"] = unit
            s.attributes = attrs
            return s
        
        # Device has two batteries; batch_evaluate should filter to one
        state_a = _state("sensor.device_bat_a", "8", device_class="battery", unit="%")
        state_b = _state("sensor.device_bat_b", "5", device_class="battery", unit="%")
        
        def meta_fn(entity_id):
            if entity_id.startswith("sensor.device"):
                return ("Mfg", "Model", "Room", "device_123")
            return None
        
        low_battery, _ = evaluator.batch_evaluate([state_a, state_b], metadata_fn=meta_fn)
        store.bulk_set_low_battery(low_battery)
        
        # After initial batch: should have only 1 (first by entity_id: sensor.device_bat_a)
        assert store.low_battery_count == 1
        assert "sensor.device_bat_a" in store._low_battery
        assert "sensor.device_bat_b" not in store._low_battery
        
        # --- STEP 2: State change event (sensor.device_bat_b drops below threshold) ---
        state_b_low = _state("sensor.device_bat_b", "3", device_class="battery", unit="%")
        
        # Simulating _handle_state_changed in __init__.py
        lb_row = evaluator.evaluate_low_battery(state_b_low, "Mfg", "Model", "Room")
        assert lb_row is not None  # It is low battery
        lb_row.device_id = "device_123"
        store.upsert_low_battery(lb_row)  # This is where AC4 must be enforced
        
        # AC4 CRITICAL: After incremental update, should STILL have only 1 battery
        # (the first by entity_id, which is sensor.device_bat_a)
        assert store.low_battery_count == 1, \
            f"AC4 VIOLATION: Expected 1 battery, got {store.low_battery_count}. " \
            f"This is the production bug: incremental updates bypass AC4 filtering."
        assert "sensor.device_bat_a" in store._low_battery
        assert "sensor.device_bat_b" not in store._low_battery
