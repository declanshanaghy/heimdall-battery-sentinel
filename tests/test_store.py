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
