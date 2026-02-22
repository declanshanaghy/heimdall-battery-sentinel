"""Tests for textual battery evaluation."""

import pytest

from custom_components.heimdall_battery_sentinel.evaluator import (
    evaluate_battery,
    evaluate_textual_battery,
)


class TestEvaluateTextualBattery:
    """Tests for evaluate_textual_battery function."""

    def test_low_textual_returns_true(self):
        """Test that 'low' textual state returns is_low=True."""
        is_low, display = evaluate_textual_battery("low")
        assert is_low is True
        assert display == "low"

    def test_low_uppercase_returns_true(self):
        """Test that 'LOW' (uppercase) returns is_low=True."""
        is_low, display = evaluate_textual_battery("LOW")
        assert is_low is True
        assert display == "low"

    def test_low_mixed_case_returns_true(self):
        """Test that 'Low' (mixed case) returns is_low=True."""
        is_low, display = evaluate_textual_battery("Low")
        assert is_low is True
        assert display == "low"

    def test_low_with_whitespace_returns_true(self):
        """Test that ' low ' (with whitespace) returns is_low=True."""
        is_low, display = evaluate_textual_battery(" low ")
        assert is_low is True
        assert display == "low"

    def test_medium_textual_returns_false(self):
        """Test that 'medium' textual state returns is_low=False."""
        is_low, display = evaluate_textual_battery("medium")
        assert is_low is False
        assert display == ""

    def test_high_textual_returns_false(self):
        """Test that 'high' textual state returns is_low=False."""
        is_low, display = evaluate_textual_battery("high")
        assert is_low is False
        assert display == ""

    def test_invalid_textual_returns_false(self):
        """Test that invalid textual states return is_low=False."""
        is_low, display = evaluate_textual_battery("unknown")
        assert is_low is False
        assert display == ""

    def test_empty_string_returns_false(self):
        """Test that empty string returns is_low=False."""
        is_low, display = evaluate_textual_battery("")
        assert is_low is False
        assert display == ""

    def test_none_returns_false(self):
        """Test that None returns is_low=False."""
        is_low, display = evaluate_textual_battery(None)
        assert is_low is False
        assert display == ""


class TestEvaluateBatteryTextualIntegration:
    """Tests for evaluate_battery function with textual states."""

    def test_textual_low_integration(self):
        """Test that textual 'low' is properly integrated."""
        result = evaluate_battery("low", None, 15)
        assert result["is_low"] is True
        assert result["display"] == "low"
        # Textual 'low' has numeric=0 for sorting purposes (lowest value)
        assert result["numeric"] == 0
        # Textual 'low' should have a severity assigned (most critical = RED)
        assert result["severity"] is not None

    def test_textual_medium_excluded(self):
        """Test that textual 'medium' is excluded."""
        result = evaluate_battery("medium", None, 15)
        assert result["is_low"] is False
        assert result["display"] == ""

    def test_textual_high_excluded(self):
        """Test that textual 'high' is excluded."""
        result = evaluate_battery("high", None, 15)
        assert result["is_low"] is False
        assert result["display"] == ""

    def test_textual_low_has_numeric_sort_value(self):
        """Test that textual 'low' has a numeric value for sorting.
        
        Textual 'low' should sort as if it's the lowest possible value.
        """
        result = evaluate_battery("low", None, 15)
        # Should have a numeric value for sorting purposes
        assert result["numeric"] is not None
        # Should be the lowest possible value (0 or similar)
        assert result["numeric"] <= 0
