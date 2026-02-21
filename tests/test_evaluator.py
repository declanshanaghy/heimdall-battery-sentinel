"""Unit tests for evaluator.py — battery evaluation rules (ADR-005)."""
import pytest
from unittest.mock import MagicMock

from custom_components.heimdall_battery_sentinel.evaluator import (
    BatteryEvaluator,
    evaluate_battery_state,
    evaluate_unavailable_state,
)
from custom_components.heimdall_battery_sentinel.const import (
    SEVERITY_RED,
    SEVERITY_ORANGE,
    SEVERITY_YELLOW,
    STATE_UNAVAILABLE,
)


# ── Helper to create mock HA State objects ────────────────────────────────────

def _state(entity_id, state_val, device_class=None, unit=None, friendly_name=None):
    s = MagicMock()
    s.entity_id = entity_id
    s.state = state_val
    attrs = {}
    if device_class:
        attrs["device_class"] = device_class
    if unit:
        attrs["unit_of_measurement"] = unit
    if friendly_name:
        attrs["friendly_name"] = friendly_name
    s.attributes = attrs
    return s


def _battery_state(entity_id, state_val, unit="%", friendly_name=None):
    return _state(entity_id, state_val, device_class="battery", unit=unit, friendly_name=friendly_name)


# ── evaluate_battery_state ────────────────────────────────────────────────────

class TestEvaluateBatteryState:
    """Test the standalone evaluate_battery_state function (ADR-005)."""

    # --- Numeric battery ---

    def test_numeric_below_threshold_included(self):
        state = _battery_state("sensor.b1", "10", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.entity_id == "sensor.b1"
        assert row.battery_numeric == 10.0
        assert row.battery_display == "10%"

    def test_numeric_at_threshold_included(self):
        state = _battery_state("sensor.b1", "15", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None

    def test_numeric_above_threshold_excluded(self):
        state = _battery_state("sensor.b1", "50", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is None

    def test_numeric_wrong_unit_excluded(self):
        """Numeric battery with unit != '%' must be excluded (ADR-005)."""
        state = _battery_state("sensor.b1", "10", unit="V")
        row = evaluate_battery_state(state, threshold=15)
        assert row is None

    def test_numeric_no_unit_excluded(self):
        state = _battery_state("sensor.b1", "10", unit=None)
        row = evaluate_battery_state(state, threshold=15)
        assert row is None

    def test_numeric_rounding(self):
        state = _battery_state("sensor.b1", "7.6", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.battery_display == "8%"  # round(7.6) = 8

    def test_numeric_rounding_down(self):
        state = _battery_state("sensor.b1", "7.4", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.battery_display == "7%"

    # --- Severity ---

    def test_severity_red(self):
        state = _battery_state("sensor.b1", "5", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row.severity == SEVERITY_RED

    def test_severity_orange(self):
        state = _battery_state("sensor.b1", "8", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row.severity == SEVERITY_ORANGE

    def test_severity_yellow(self):
        state = _battery_state("sensor.b1", "12", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row.severity == SEVERITY_YELLOW

    # --- Textual battery ---

    def test_textual_low_included(self):
        state = _battery_state("sensor.b2", "low", unit=None)
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.battery_display == "low"
        assert row.battery_numeric is None
        assert row.severity is None

    def test_textual_medium_excluded(self):
        state = _battery_state("sensor.b2", "medium", unit=None)
        row = evaluate_battery_state(state, threshold=15)
        assert row is None

    def test_textual_high_excluded(self):
        state = _battery_state("sensor.b2", "high", unit=None)
        row = evaluate_battery_state(state, threshold=15)
        assert row is None

    def test_textual_case_insensitive_low(self):
        state = _battery_state("sensor.b2", "LOW", unit=None)
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None

    def test_textual_case_insensitive_medium_excluded(self):
        state = _battery_state("sensor.b2", "Medium", unit=None)
        row = evaluate_battery_state(state, threshold=15)
        assert row is None

    # --- Non-battery device_class ---

    def test_non_battery_device_class_excluded(self):
        state = _state("sensor.temp", "20", device_class="temperature", unit="°C")
        row = evaluate_battery_state(state, threshold=15)
        assert row is None

    def test_no_device_class_excluded(self):
        state = _state("sensor.generic", "10", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is None

    # --- Unavailable state ---

    def test_unavailable_state_excluded(self):
        state = _battery_state("sensor.b1", STATE_UNAVAILABLE, unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is None

    # --- None state ---

    def test_none_state_returns_none(self):
        row = evaluate_battery_state(None, threshold=15)
        assert row is None

    # --- Friendly name ---

    def test_friendly_name_extracted(self):
        state = _battery_state("sensor.b1", "10", unit="%", friendly_name="My Battery")
        row = evaluate_battery_state(state, threshold=15)
        assert row.friendly_name == "My Battery"

    def test_friendly_name_fallback_to_entity_id(self):
        state = _battery_state("sensor.b1", "10", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row.friendly_name == "sensor.b1"

    # --- Metadata propagation ---

    def test_metadata_propagated(self):
        state = _battery_state("sensor.b1", "10", unit="%")
        row = evaluate_battery_state(state, threshold=15, manufacturer="Acme", model="X1", area="Living Room")
        assert row.manufacturer == "Acme"
        assert row.model == "X1"
        assert row.area == "Living Room"


# ── evaluate_unavailable_state ────────────────────────────────────────────────

class TestEvaluateUnavailableState:
    def test_unavailable_included(self):
        state = _state("light.lamp", STATE_UNAVAILABLE)
        row = evaluate_unavailable_state(state)
        assert row is not None
        assert row.entity_id == "light.lamp"

    def test_non_unavailable_excluded(self):
        state = _state("light.lamp", "on")
        row = evaluate_unavailable_state(state)
        assert row is None

    def test_none_state_returns_none(self):
        row = evaluate_unavailable_state(None)
        assert row is None

    def test_all_entities_considered(self):
        """Unavailable check applies to ALL entities, not just battery."""
        state = _state("sensor.temp", STATE_UNAVAILABLE, device_class="temperature")
        row = evaluate_unavailable_state(state)
        assert row is not None

    def test_metadata_propagated(self):
        state = _state("light.lamp", STATE_UNAVAILABLE)
        row = evaluate_unavailable_state(state, manufacturer="Philips", area="Kitchen")
        assert row.manufacturer == "Philips"
        assert row.area == "Kitchen"


# ── BatteryEvaluator class ────────────────────────────────────────────────────

class TestBatteryEvaluator:
    def test_initial_threshold(self):
        evaluator = BatteryEvaluator(threshold=20)
        assert evaluator.threshold == 20

    def test_threshold_setter(self):
        evaluator = BatteryEvaluator(threshold=20)
        evaluator.threshold = 30
        assert evaluator.threshold == 30

    def test_evaluate_low_battery(self):
        evaluator = BatteryEvaluator(threshold=15)
        state = _battery_state("sensor.b1", "10", unit="%")
        row = evaluator.evaluate_low_battery(state)
        assert row is not None

    def test_evaluate_unavailable(self):
        evaluator = BatteryEvaluator(threshold=15)
        state = _state("light.lamp", STATE_UNAVAILABLE)
        row = evaluator.evaluate_unavailable(state)
        assert row is not None

    def test_batch_evaluate_returns_both_lists(self):
        evaluator = BatteryEvaluator(threshold=15)
        states = [
            _battery_state("sensor.low", "5", unit="%"),
            _battery_state("sensor.ok", "50", unit="%"),
            _state("light.lamp", STATE_UNAVAILABLE),
            _state("switch.plug", "on"),
        ]
        low_battery, unavailable = evaluator.batch_evaluate(states)
        assert len(low_battery) == 1
        assert low_battery[0].entity_id == "sensor.low"
        assert len(unavailable) == 1
        assert unavailable[0].entity_id == "light.lamp"

    def test_batch_evaluate_with_metadata_fn(self):
        evaluator = BatteryEvaluator(threshold=15)
        states = [_battery_state("sensor.low", "5", unit="%")]

        def meta_fn(entity_id):
            return ("Acme", "X1", "Bedroom")

        low_battery, _ = evaluator.batch_evaluate(states, metadata_fn=meta_fn)
        assert low_battery[0].manufacturer == "Acme"
        assert low_battery[0].area == "Bedroom"

    def test_batch_evaluate_empty_states(self):
        evaluator = BatteryEvaluator(threshold=15)
        low_battery, unavailable = evaluator.batch_evaluate([])
        assert low_battery == []
        assert unavailable == []
