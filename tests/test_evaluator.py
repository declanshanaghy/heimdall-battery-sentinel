"""Unit tests for evaluator.py — battery evaluation rules (ADR-005)."""
import pytest
from unittest.mock import MagicMock

from custom_components.heimdall_battery_sentinel.evaluator import (
    BatteryEvaluator,
    evaluate_battery_state,
    evaluate_unavailable_state,
)
from custom_components.heimdall_battery_sentinel.const import (
    SEVERITY_CRITICAL,
    SEVERITY_CRITICAL_ICON,
    SEVERITY_NOTICE,
    SEVERITY_NOTICE_ICON,
    SEVERITY_WARNING,
    SEVERITY_WARNING_ICON,
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

    def test_severity_critical_ratio_based(self):
        """Test ratio-based critical severity (ratio 0-33, inclusive)."""
        # battery=3, threshold=15: ratio = (3/15)*100 = 20 <= 33 → critical
        state = _battery_state("sensor.b1", "3", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row.severity == SEVERITY_CRITICAL
        assert row.severity_icon == SEVERITY_CRITICAL_ICON

    def test_severity_warning_ratio_based(self):
        """Test ratio-based warning severity (ratio 34-66)."""
        # battery=8, threshold=15: ratio = (8/15)*100 = 53.33 → warning
        state = _battery_state("sensor.b1", "8", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row.severity == SEVERITY_WARNING
        assert row.severity_icon == SEVERITY_WARNING_ICON

    def test_severity_notice_ratio_based(self):
        """Test ratio-based notice severity (ratio 67-100)."""
        # battery=12, threshold=15: ratio = (12/15)*100 = 80 >= 67 → notice
        state = _battery_state("sensor.b1", "12", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row.severity == SEVERITY_NOTICE
        assert row.severity_icon == SEVERITY_NOTICE_ICON

    # --- Textual battery ---

    def test_textual_low_included(self):
        """AC3: Textual 'low' batteries have fixed Critical severity."""
        state = _battery_state("sensor.b2", "low", unit=None)
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.battery_display == "low"
        assert row.battery_numeric is None
        assert row.severity == SEVERITY_CRITICAL
        assert row.severity_icon == SEVERITY_CRITICAL_ICON

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
            # metadata_fn MUST return 4-tuple: (manufacturer, model, area, device_id)
            return ("Acme", "X1", "Bedroom", "device_acme_001")

        low_battery, _ = evaluator.batch_evaluate(states, metadata_fn=meta_fn)
        assert low_battery[0].manufacturer == "Acme"
        assert low_battery[0].area == "Bedroom"
        assert low_battery[0].device_id == "device_acme_001"

    def test_batch_evaluate_empty_states(self):
        evaluator = BatteryEvaluator(threshold=15)
        low_battery, unavailable = evaluator.batch_evaluate([])
        assert low_battery == []
        assert unavailable == []

    # --- AC4: Device-level filtering (one battery per device) ---

    def test_device_with_two_batteries_both_low_returns_first_by_entity_id(self):
        """AC4: Device with two low batteries → return only first by entity_id ascending."""
        evaluator = BatteryEvaluator(threshold=15)
        device_id = "device_abc123"
        
        # Two batteries for the same device, both below threshold
        state1 = _battery_state("sensor.phone_battery_level", "8", unit="%")
        state2 = _battery_state("sensor.phone_main_battery", "5", unit="%")
        
        def meta_fn(entity_id):
            # Both entities belong to the same device
            if entity_id in ["sensor.phone_battery_level", "sensor.phone_main_battery"]:
                return ("Apple", "iPhone", "Bedroom", device_id)
            return (None, None, None, None)
        
        low_battery, _ = evaluator.batch_evaluate([state1, state2], metadata_fn=meta_fn)
        
        # Should return only ONE battery: sensor.phone_battery_level (first by entity_id ascending)
        assert len(low_battery) == 1
        assert low_battery[0].entity_id == "sensor.phone_battery_level"
        assert low_battery[0].battery_numeric == 8.0

    def test_device_with_two_batteries_one_low_returns_low(self):
        """AC4: Device with one low and one ok battery → return only the low one."""
        evaluator = BatteryEvaluator(threshold=15)
        device_id = "device_xyz789"
        
        state1 = _battery_state("sensor.device_battery_main", "8", unit="%")
        state2 = _battery_state("sensor.device_battery_secondary", "50", unit="%")
        
        def meta_fn(entity_id):
            if entity_id in ["sensor.device_battery_main", "sensor.device_battery_secondary"]:
                return ("Manufacturer", "Model", "Kitchen", device_id)
            return (None, None, None, None)
        
        low_battery, _ = evaluator.batch_evaluate([state1, state2], metadata_fn=meta_fn)
        
        # Should return only the low one
        assert len(low_battery) == 1
        assert low_battery[0].entity_id == "sensor.device_battery_main"

    def test_multiple_devices_with_multiple_batteries_each(self):
        """AC4: Multiple devices each with multiple batteries → return first per device."""
        evaluator = BatteryEvaluator(threshold=15)
        
        # Device A: two batteries
        state_a1 = _battery_state("sensor.device_a_bat1", "5", unit="%")
        state_a2 = _battery_state("sensor.device_a_bat2", "8", unit="%")
        
        # Device B: two batteries
        state_b1 = _battery_state("sensor.device_b_bat1", "10", unit="%")
        state_b2 = _battery_state("sensor.device_b_bat2", "12", unit="%")
        
        def meta_fn(entity_id):
            if entity_id.startswith("sensor.device_a"):
                return ("MfgA", "ModelA", "Room1", "device_a")
            elif entity_id.startswith("sensor.device_b"):
                return ("MfgB", "ModelB", "Room2", "device_b")
            return (None, None, None, None)
        
        low_battery, _ = evaluator.batch_evaluate([state_a1, state_a2, state_b1, state_b2], metadata_fn=meta_fn)
        
        # Should return 2 rows: one per device, first by entity_id
        assert len(low_battery) == 2
        entity_ids = {row.entity_id for row in low_battery}
        assert "sensor.device_a_bat1" in entity_ids  # first for device A
        assert "sensor.device_b_bat1" in entity_ids  # first for device B

    def test_batch_evaluate_with_metadata_fn_extended_format(self):
        """AC4: metadata_fn returns 4-tuple with device_id."""
        evaluator = BatteryEvaluator(threshold=15)
        states = [_battery_state("sensor.low", "5", unit="%")]

        def meta_fn(entity_id):
            # Extended format: (manufacturer, model, area, device_id)
            return ("Acme", "X1", "Bedroom", "device_123")

        low_battery, _ = evaluator.batch_evaluate(states, metadata_fn=meta_fn)
        assert low_battery[0].manufacturer == "Acme"
        assert low_battery[0].area == "Bedroom"


# ── Story 2.2: Textual Battery Monitoring (AC Validation) ──────────────────

class TestStory22TextualBatteryAC:
    """Comprehensive AC validation for Story 2.2: Textual Battery Monitoring.
    
    AC1: Only include textual battery entities with state=='low'
    AC2: Exclude medium/high textual states
    AC3: Display 'low' state label consistently
    AC4: Apply proper color coding per severity rules
    AC5: Maintain server-side sorting functionality
    """

    # AC1: Only include textual battery entities with state=='low'
    def test_ac1_textual_low_only(self):
        """AC1: Only textual 'low' batteries are included."""
        evaluator = BatteryEvaluator(threshold=15)
        states = [
            _battery_state("sensor.textual_low", "low", unit=None),
        ]
        low_battery, _ = evaluator.batch_evaluate(states)
        assert len(low_battery) == 1
        assert low_battery[0].battery_display == "low"

    # AC2: Exclude medium/high textual states
    def test_ac2_exclude_medium(self):
        """AC2: Textual 'medium' batteries are excluded."""
        evaluator = BatteryEvaluator(threshold=15)
        states = [
            _battery_state("sensor.textual_medium", "medium", unit=None),
        ]
        low_battery, _ = evaluator.batch_evaluate(states)
        assert len(low_battery) == 0

    def test_ac2_exclude_high(self):
        """AC2: Textual 'high' batteries are excluded."""
        evaluator = BatteryEvaluator(threshold=15)
        states = [
            _battery_state("sensor.textual_high", "high", unit=None),
        ]
        low_battery, _ = evaluator.batch_evaluate(states)
        assert len(low_battery) == 0

    # AC3: Display 'low' state label consistently
    def test_ac3_textual_low_display_label(self):
        """AC3: Textual 'low' battery displays as 'low' label."""
        state = _battery_state("sensor.t1", "low", unit=None, friendly_name="Device 1")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.battery_display == "low"
        assert row.battery_numeric is None

    def test_ac3_case_insensitive_display(self):
        """AC3: Case-insensitive input normalizes to 'low' label."""
        state = _battery_state("sensor.t2", "LOW", unit=None, friendly_name="Device 2")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.battery_display == "low"

    # AC4: Apply proper color coding per severity rules (updated for story 2-3)
    def test_ac4_textual_has_critical_severity(self):
        """AC3/Story 2-3: Textual 'low' has fixed Critical severity."""
        state = _battery_state("sensor.t3", "low", unit=None)
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_CRITICAL  # Textual has fixed critical severity
        assert row.severity_icon == SEVERITY_CRITICAL_ICON

    def test_ac4_numeric_has_severity_coloring(self):
        """AC2/Story 2-3: Numeric batteries have ratio-based severity coloring."""
        evaluator = BatteryEvaluator(threshold=15)
        
        numeric_state = _battery_state("sensor.num", "10", unit="%")
        numeric_row = evaluator.evaluate_low_battery(numeric_state)
        assert numeric_row is not None
        assert numeric_row.severity in {SEVERITY_CRITICAL, SEVERITY_WARNING, SEVERITY_NOTICE}
        assert numeric_row.severity_icon is not None  # Numeric has severity icon
        
        textual_state = _battery_state("sensor.text", "low", unit=None)
        textual_row = evaluator.evaluate_low_battery(textual_state)
        assert textual_row is not None
        assert textual_row.severity == SEVERITY_CRITICAL  # Textual has critical severity

    # AC5: Maintain server-side sorting functionality
    def test_ac5_sorting_textual_with_numeric(self):
        """AC5: Sorting works correctly when mixing numeric and textual batteries."""
        evaluator = BatteryEvaluator(threshold=15)
        
        states = [
            _battery_state("sensor.t1", "low", unit=None, friendly_name="Textual Device"),
            _battery_state("sensor.n1", "10", unit="%", friendly_name="Numeric Device"),
        ]
        low_battery, _ = evaluator.batch_evaluate(states)
        
        # Both should be in results (10% is below 15% threshold)
        assert len(low_battery) == 2
        
        # Verify they can be sorted without errors
        from custom_components.heimdall_battery_sentinel.models import sort_low_battery_rows
        sorted_rows = sort_low_battery_rows(low_battery, "battery_level", "asc")
        assert len(sorted_rows) == 2
        # Numeric sorts first, textual last
        assert sorted_rows[0].battery_numeric == 10.0
        assert sorted_rows[1].battery_numeric is None


# ── Story 2-3: Severity Calculation (Ratio-Based) ──────────────────────────────────

class TestStory23SeverityCalculation:
    """Test ratio-based severity calculation per AC1, AC2, AC3, AC5 (Story 2-3)."""

    # AC1: Severity is calculated based on ratio = (battery_level / threshold) * 100

    def test_ac1_ratio_calculation_critical_boundary(self):
        """AC1: Ratio-based calculation at critical/warning boundary (ratio=33)."""
        # battery=4.95, threshold=15: ratio = (4.95/15)*100 = 33% → critical (inclusive)
        state = _battery_state("sensor.b1", "4.95", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_CRITICAL

    def test_ac1_ratio_calculation_warning_boundary(self):
        """AC1: Ratio-based calculation at warning/notice boundary (ratio=66)."""
        # battery=9.9, threshold=15: ratio = (9.9/15)*100 = 66% → warning (inclusive)
        state = _battery_state("sensor.b2", "9.9", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_WARNING

    def test_ac1_ratio_calculation_critical_to_warning(self):
        """AC1: Ratio transitions from critical to warning at ratio > 33."""
        # battery=5.1, threshold=15: ratio = (5.1/15)*100 = 34% → warning
        state = _battery_state("sensor.b3", "5.1", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_WARNING

    def test_ac1_ratio_calculation_warning_to_notice(self):
        """AC1: Ratio transitions from warning to notice at ratio > 66."""
        # battery=10.05, threshold=15: ratio = (10.05/15)*100 = 67% → notice
        state = _battery_state("sensor.b4", "10.05", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_NOTICE

    # AC2: Severity levels with correct colors and icons

    def test_ac2_critical_severity_icon(self):
        """AC2: Critical severity has mdi:battery-alert icon."""
        state = _battery_state("sensor.c1", "3", unit="%")  # ratio=20 → critical
        row = evaluate_battery_state(state, threshold=15)
        assert row.severity == SEVERITY_CRITICAL
        assert row.severity_icon == SEVERITY_CRITICAL_ICON
        assert row.severity_icon == "mdi:battery-alert"

    def test_ac2_warning_severity_icon(self):
        """AC2: Warning severity has mdi:battery-low icon."""
        state = _battery_state("sensor.w1", "8", unit="%")  # ratio=53.3 → warning
        row = evaluate_battery_state(state, threshold=15)
        assert row.severity == SEVERITY_WARNING
        assert row.severity_icon == SEVERITY_WARNING_ICON
        assert row.severity_icon == "mdi:battery-low"

    def test_ac2_notice_severity_icon(self):
        """AC2: Notice severity has mdi:battery-medium icon."""
        state = _battery_state("sensor.n1", "12", unit="%")  # ratio=80 → notice
        row = evaluate_battery_state(state, threshold=15)
        assert row.severity == SEVERITY_NOTICE
        assert row.severity_icon == SEVERITY_NOTICE_ICON
        assert row.severity_icon == "mdi:battery-medium"

    # AC3: Textual batteries with fixed Critical severity

    def test_ac3_textual_low_fixed_critical_severity(self):
        """AC3: Textual 'low' batteries have fixed Critical severity."""
        state = _battery_state("sensor.text_low", "low", unit=None)
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.battery_numeric is None
        assert row.severity == SEVERITY_CRITICAL
        assert row.severity_icon == SEVERITY_CRITICAL_ICON

    def test_ac3_textual_medium_and_high_excluded(self):
        """AC3: Only textual 'low' is included, not 'medium' or 'high'."""
        medium_state = _battery_state("sensor.text_med", "medium", unit=None)
        high_state = _battery_state("sensor.text_high", "high", unit=None)
        
        med_row = evaluate_battery_state(medium_state, threshold=15)
        high_row = evaluate_battery_state(high_state, threshold=15)
        
        assert med_row is None
        assert high_row is None

    # AC5: Severity uses current configurable threshold

    def test_ac5_threshold_change_affects_severity(self):
        """AC5: Different thresholds produce different severity for same battery level."""
        state = _battery_state("sensor.flex", "6", unit="%")
        
        # Threshold=15: ratio = (6/15)*100 = 40 → warning
        row1 = evaluate_battery_state(state, threshold=15)
        assert row1.severity == SEVERITY_WARNING
        
        # Threshold=20: ratio = (6/20)*100 = 30 → critical
        row2 = evaluate_battery_state(state, threshold=20)
        assert row2.severity == SEVERITY_CRITICAL

    def test_ac5_evaluator_threshold_property(self):
        """AC5: BatteryEvaluator threshold property updates severity calculation."""
        state = _battery_state("sensor.dyn", "10", unit="%")
        
        evaluator = BatteryEvaluator(threshold=15)
        # ratio = (10/15)*100 = 66.67 → notice (just barely)
        row1 = evaluator.evaluate_low_battery(state)
        assert row1.severity == SEVERITY_NOTICE
        
        # Change threshold to 20
        evaluator.threshold = 20
        # ratio = (10/20)*100 = 50 → warning
        row2 = evaluator.evaluate_low_battery(state)
        assert row2.severity == SEVERITY_WARNING

    # Comprehensive ratio coverage tests

    def test_ratio_min_value(self):
        """Test ratio at 0% (battery=0, threshold=15)."""
        state = _battery_state("sensor.zero", "0", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_CRITICAL

    def test_ratio_max_at_critical_threshold(self):
        """Test ratio at exactly 33% (battery=4.95, threshold=15)."""
        state = _battery_state("sensor.crit33", "4.95", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_CRITICAL

    def test_ratio_min_warning(self):
        """Test ratio at 34% (battery=5.1, threshold=15)."""
        state = _battery_state("sensor.warn34", "5.1", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_WARNING

    def test_ratio_max_warning(self):
        """Test ratio at 66% (battery=9.9, threshold=15)."""
        state = _battery_state("sensor.warn66", "9.9", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_WARNING

    def test_ratio_min_notice(self):
        """Test ratio at 67% (battery=10.05, threshold=15)."""
        state = _battery_state("sensor.notice67", "10.05", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_NOTICE

    def test_ratio_max_notice(self):
        """Test ratio at 100% (battery=15, threshold=15)."""
        state = _battery_state("sensor.notice100", "15", unit="%")
        row = evaluate_battery_state(state, threshold=15)
        assert row is not None
        assert row.severity == SEVERITY_NOTICE

    def test_different_threshold_critical_range(self):
        """Test critical range (0-33%) with threshold=20."""
        # battery=6, threshold=20: ratio=30 → critical
        state = _battery_state("sensor.th20_crit", "6", unit="%")
        row = evaluate_battery_state(state, threshold=20)
        assert row.severity == SEVERITY_CRITICAL

    def test_different_threshold_warning_range(self):
        """Test warning range (34-66%) with threshold=20."""
        # battery=10, threshold=20: ratio=50 → warning
        state = _battery_state("sensor.th20_warn", "10", unit="%")
        row = evaluate_battery_state(state, threshold=20)
        assert row.severity == SEVERITY_WARNING

    def test_different_threshold_notice_range(self):
        """Test notice range (67-100%) with threshold=20."""
        # battery=15, threshold=20: ratio=75 → notice
        state = _battery_state("sensor.th20_notice", "15", unit="%")
        row = evaluate_battery_state(state, threshold=20)
        assert row.severity == SEVERITY_NOTICE
