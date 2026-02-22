"""Tests for numeric battery evaluation."""

import pytest

from custom_components.heimdall_battery_sentinel.evaluator import (
    evaluate_battery,
    evaluate_numeric_battery,
)
from custom_components.heimdall_battery_sentinel.models import Severity


class TestEvaluateNumericBattery:
    """Tests for evaluate_numeric_battery function."""

    def test_numeric_battery_within_threshold_is_low(self):
        """Test numeric battery within threshold is flagged as low."""
        is_low, numeric, severity = evaluate_numeric_battery("14", "%", 15)
        
        assert is_low is True
        assert numeric == 14.0
        # ratio = (14/15)*100 = 93.33... → YELLOW (67-100)
        assert severity == Severity.YELLOW

    def test_numeric_battery_below_threshold_is_low(self):
        """Test numeric battery below threshold is flagged as low."""
        is_low, numeric, severity = evaluate_numeric_battery("10", "%", 15)
        
        assert is_low is True
        assert numeric == 10.0
        # ratio = (10/15)*100 = 66.66... → YELLOW (67-100)
        assert severity == Severity.YELLOW

    def test_numeric_battery_at_threshold_is_low(self):
        """Test numeric battery at threshold is flagged as low."""
        is_low, numeric, severity = evaluate_numeric_battery("15", "%", 15)
        
        assert is_low is True
        assert numeric == 15.0
        # ratio = (15/15)*100 = 100 → YELLOW (67-100)
        assert severity == Severity.YELLOW

    def test_numeric_battery_above_threshold_not_low(self):
        """Test numeric battery above threshold is not low."""
        is_low, numeric, severity = evaluate_numeric_battery("16", "%", 15)
        
        assert is_low is False
        assert numeric == 16.0
        assert severity is None

    def test_numeric_battery_rounding(self):
        """Test numeric battery rounding - 14.7% rounds to 15%."""
        # The display value should round
        result = evaluate_battery("14.7", "%", 15)
        
        assert result["is_low"] is True
        assert result["numeric"] == 14.7
        # The display is rounded
        assert result["display"] == "15%"

    def test_numeric_battery_rounds_down(self):
        """Test numeric battery rounding - 14.4% rounds to 14%."""
        result = evaluate_battery("14.4", "%", 15)
        
        assert result["is_low"] is True
        assert result["display"] == "14%"

    def test_numeric_battery_rounds_up(self):
        """Test numeric battery rounding - Python uses banker's rounding."""
        # Python's round() uses banker's rounding (round half to even)
        # 14.5 rounds to 14 (even), 15.5 rounds to 16 (even)
        result = evaluate_battery("14.5", "%", 15)
        
        assert result["is_low"] is True
        # 14.5 rounds to 14 (banker's rounding)
        assert result["display"] == "14%"

    def test_wrong_unit_not_low(self):
        """Test entities with wrong unit are not considered low."""
        is_low, numeric, severity = evaluate_numeric_battery("14", "V", 15)
        
        assert is_low is False
        assert numeric is None
        assert severity is None

    def test_no_unit_not_low(self):
        """Test entities without unit are not considered low."""
        is_low, numeric, severity = evaluate_numeric_battery("14", None, 15)
        
        assert is_low is False
        assert numeric is None
        assert severity is None

    def test_invalid_state_not_low(self):
        """Test invalid state values are not considered low."""
        is_low, numeric, severity = evaluate_numeric_battery("unknown", "%", 15)
        
        assert is_low is False
        assert numeric is None
        assert severity is None

    def test_empty_state_not_low(self):
        """Test empty state values are not considered low."""
        is_low, numeric, severity = evaluate_numeric_battery("", "%", 15)
        
        assert is_low is False
        assert numeric is None
        assert severity is None

    def test_none_state_not_low(self):
        """Test None state values are not considered low."""
        is_low, numeric, severity = evaluate_numeric_battery(None, "%", 15)
        
        assert is_low is False
        assert numeric is None
        assert severity is None

    def test_severity_red_for_very_low(self):
        """Test severity is RED for very low batteries (ratio 0-33).
        
        With threshold 15, values 0-4 give ratio 0-26.66... → RED.
        """
        # ratio = (4/15)*100 = 26.66... → RED (0-33 inclusive)
        is_low, numeric, severity = evaluate_numeric_battery("4", "%", 15)
        
        assert is_low is True
        assert severity == Severity.RED

    def test_severity_orange_for_low(self):
        """Test severity is ORANGE for low batteries (ratio 34-66).
        
        With threshold 15, values 5-9 give ratio 33.33...-60 → ORANGE.
        """
        # ratio = (7/15)*100 = 46.66... → ORANGE (34-66)
        is_low, numeric, severity = evaluate_numeric_battery("7", "%", 15)
        
        assert is_low is True
        assert severity == Severity.ORANGE

    def test_severity_yellow_for_moderate(self):
        """Test severity is YELLOW for moderate low batteries (ratio 67-100)."""
        # ratio = (25/30)*100 = 83.33... → YELLOW (67-100)
        is_low, numeric, severity = evaluate_numeric_battery("25", "%", 30)
        
        assert is_low is True
        assert severity == Severity.YELLOW

    def test_custom_threshold(self):
        """Test custom threshold works correctly."""
        is_low, numeric, severity = evaluate_numeric_battery("20", "%", 25)
        
        assert is_low is True
        assert numeric == 20.0


class TestEvaluateBattery:
    """Tests for evaluate_battery function."""

    def test_numeric_low_battery_returns_correct_dict(self):
        """Test numeric low battery returns correct dictionary structure."""
        # ratio = (10/15)*100 = 66.66... → YELLOW (67-100)
        result = evaluate_battery("10", "%", 15)
        
        assert result["is_low"] is True
        assert result["display"] == "10%"
        assert result["numeric"] == 10.0
        assert result["severity"] == Severity.YELLOW

    def test_numeric_not_low_returns_empty_display(self):
        """Test numeric not low returns empty display."""
        result = evaluate_battery("50", "%", 15)
        
        assert result["is_low"] is False
        assert result["display"] == ""
        assert result["numeric"] is None
        assert result["severity"] is None
