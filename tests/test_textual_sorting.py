"""Tests for textual battery sorting."""

import pytest

from custom_components.heimdall_battery_sentinel.store import (
    _sort_rows,
    get_store,
)
from custom_components.heimdall_battery_sentinel.models import LowBatteryRow, Severity
from datetime import datetime


class TestTextualBatterySorting:
    """Tests for sorting textual battery rows."""

    def test_textual_low_sorts_with_numeric_zero(self):
        """Test that textual 'low' batteries sort correctly with numeric=0."""
        # Create rows with textual and numeric batteries
        textual_row = LowBatteryRow(
            entity_id="sensor.test_textual",
            friendly_name="Test Textual",
            manufacturer=None,
            model=None,
            area="Living Room",
            battery_display="low",
            battery_numeric=0,  # Textual 'low' gets 0
            severity=Severity.RED,
            updated_at=datetime.now(),
        )
        
        numeric_row = LowBatteryRow(
            entity_id="sensor.test_numeric",
            friendly_name="Test Numeric",
            manufacturer=None,
            model=None,
            area="Bedroom",
            battery_display="15%",
            battery_numeric=15,
            severity=Severity.YELLOW,
            updated_at=datetime.now(),
        )
        
        # Sort by battery_level ascending - textual should come first (0 < 15)
        sorted_rows = _sort_rows([numeric_row, textual_row], "battery_level", "asc")
        assert sorted_rows[0].entity_id == "sensor.test_textual"
        assert sorted_rows[1].entity_id == "sensor.test_numeric"
        
        # Sort by battery_level descending - numeric should come first (15 > 0)
        sorted_rows = _sort_rows([numeric_row, textual_row], "battery_level", "desc")
        assert sorted_rows[0].entity_id == "sensor.test_numeric"
        assert sorted_rows[1].entity_id == "sensor.test_textual"

    def test_multiple_textual_batteries_sort_by_name(self):
        """Test that multiple textual batteries sort by friendly_name tiebreaker."""
        row_a = LowBatteryRow(
            entity_id="sensor.device_b",
            friendly_name="Beta Device",
            manufacturer=None,
            model=None,
            area=None,
            battery_display="low",
            battery_numeric=0,
            severity=Severity.RED,
            updated_at=datetime.now(),
        )
        
        row_b = LowBatteryRow(
            entity_id="sensor.device_a",
            friendly_name="Alpha Device",
            manufacturer=None,
            model=None,
            area=None,
            battery_display="low",
            battery_numeric=0,
            severity=Severity.RED,
            updated_at=datetime.now(),
        )
        
        sorted_rows = _sort_rows([row_a, row_b], "battery_level", "asc")
        # Should sort by friendly_name tiebreaker: Alpha < Beta
        assert sorted_rows[0].friendly_name == "Alpha Device"
        assert sorted_rows[1].friendly_name == "Beta Device"

    def test_textual_battery_display_consistency(self):
        """Test that textual 'low' displays consistently as 'low'."""
        # This is already tested in evaluator tests, but verify integration
        from custom_components.heimdall_battery_sentinel.evaluator import evaluate_battery
        
        result = evaluate_battery("low", None, 15)
        assert result["display"] == "low"
        
        result = evaluate_battery("LOW", None, 15)
        assert result["display"] == "low"
        
        result = evaluate_battery("Low", None, 15)
        assert result["display"] == "low"
