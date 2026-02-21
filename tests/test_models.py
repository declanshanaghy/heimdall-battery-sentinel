"""Unit tests for models.py — data models and sort logic."""
import pytest
from datetime import datetime

from custom_components.heimdall_battery_sentinel.models import (
    LowBatteryRow,
    UnavailableRow,
    compute_severity,
    sort_low_battery_rows,
    sort_unavailable_rows,
)
from custom_components.heimdall_battery_sentinel.const import (
    SEVERITY_RED,
    SEVERITY_ORANGE,
    SEVERITY_YELLOW,
    SORT_DIR_ASC,
    SORT_DIR_DESC,
    SORT_FIELD_BATTERY_LEVEL,
    SORT_FIELD_FRIENDLY_NAME,
)


# ── compute_severity ─────────────────────────────────────────────────────────

class TestComputeSeverity:
    def test_red_at_zero(self):
        assert compute_severity(0) == SEVERITY_RED

    def test_red_at_threshold(self):
        assert compute_severity(5) == SEVERITY_RED

    def test_orange_at_six(self):
        assert compute_severity(6) == SEVERITY_ORANGE

    def test_orange_at_ten(self):
        assert compute_severity(10) == SEVERITY_ORANGE

    def test_yellow_at_eleven(self):
        assert compute_severity(11) == SEVERITY_YELLOW

    def test_yellow_at_threshold_15(self):
        assert compute_severity(15) == SEVERITY_YELLOW

    def test_yellow_at_100(self):
        assert compute_severity(100) == SEVERITY_YELLOW


# ── LowBatteryRow ────────────────────────────────────────────────────────────

class TestLowBatteryRow:
    def _make(self, **kwargs):
        defaults = dict(
            entity_id="sensor.battery1",
            friendly_name="Battery 1",
            battery_display="10%",
            battery_numeric=10.0,
            severity=SEVERITY_ORANGE,
        )
        defaults.update(kwargs)
        return LowBatteryRow(**defaults)

    def test_as_dict_has_required_keys(self):
        row = self._make()
        d = row.as_dict()
        assert "entity_id" in d
        assert "friendly_name" in d
        assert "battery_display" in d
        assert "battery_numeric" in d
        assert "severity" in d
        assert "manufacturer" in d
        assert "model" in d
        assert "area" in d
        assert "updated_at" in d

    def test_as_dict_values(self):
        row = self._make(battery_display="10%", battery_numeric=10.0, severity=SEVERITY_ORANGE)
        d = row.as_dict()
        assert d["entity_id"] == "sensor.battery1"
        assert d["battery_display"] == "10%"
        assert d["battery_numeric"] == 10.0
        assert d["severity"] == SEVERITY_ORANGE

    def test_textual_row_none_fields(self):
        row = self._make(battery_display="low", battery_numeric=None, severity=None)
        d = row.as_dict()
        assert d["battery_numeric"] is None
        assert d["severity"] is None

    def test_updated_at_is_string(self):
        row = self._make()
        d = row.as_dict()
        # Should be a parseable ISO string
        datetime.fromisoformat(d["updated_at"])


# ── UnavailableRow ───────────────────────────────────────────────────────────

class TestUnavailableRow:
    def test_as_dict_has_required_keys(self):
        row = UnavailableRow(entity_id="light.lamp", friendly_name="Lamp")
        d = row.as_dict()
        for key in ("entity_id", "friendly_name", "manufacturer", "model", "area", "updated_at"):
            assert key in d

    def test_as_dict_values(self):
        row = UnavailableRow(entity_id="light.lamp", friendly_name="Lamp", area="Living Room")
        d = row.as_dict()
        assert d["entity_id"] == "light.lamp"
        assert d["area"] == "Living Room"


# ── sort_low_battery_rows ─────────────────────────────────────────────────────

def _lb(entity_id, friendly_name, battery_numeric=None, battery_display="low", area=None, manufacturer=None):
    return LowBatteryRow(
        entity_id=entity_id,
        friendly_name=friendly_name,
        battery_display=battery_display,
        battery_numeric=battery_numeric,
        area=area,
        manufacturer=manufacturer,
    )


class TestSortLowBatteryRows:
    def test_sort_by_battery_level_asc(self):
        rows = [
            _lb("s.b", "B", battery_numeric=10.0, battery_display="10%"),
            _lb("s.a", "A", battery_numeric=5.0, battery_display="5%"),
            _lb("s.c", "C", battery_numeric=15.0, battery_display="15%"),
        ]
        result = sort_low_battery_rows(rows, SORT_FIELD_BATTERY_LEVEL, SORT_DIR_ASC)
        assert [r.battery_numeric for r in result] == [5.0, 10.0, 15.0]

    def test_sort_by_battery_level_desc(self):
        rows = [
            _lb("s.b", "B", battery_numeric=10.0, battery_display="10%"),
            _lb("s.a", "A", battery_numeric=5.0, battery_display="5%"),
        ]
        result = sort_low_battery_rows(rows, SORT_FIELD_BATTERY_LEVEL, SORT_DIR_DESC)
        assert result[0].battery_numeric == 10.0

    def test_sort_by_friendly_name_asc(self):
        rows = [
            _lb("s.b", "Zebra", battery_display="low"),
            _lb("s.a", "Apple", battery_display="low"),
        ]
        result = sort_low_battery_rows(rows, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC)
        assert result[0].friendly_name == "Apple"

    def test_sort_by_friendly_name_case_insensitive(self):
        rows = [
            _lb("s.b", "apple", battery_display="low"),
            _lb("s.a", "BANANA", battery_display="low"),
        ]
        result = sort_low_battery_rows(rows, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC)
        assert result[0].friendly_name == "apple"

    def test_sort_by_area_asc(self):
        rows = [
            _lb("s.b", "B", area="Kitchen"),
            _lb("s.a", "A", area="Bedroom"),
        ]
        result = sort_low_battery_rows(rows, "area", SORT_DIR_ASC)
        assert result[0].area == "Bedroom"

    def test_sort_textual_battery_last(self):
        """Textual 'low' rows should sort after numeric rows when sorting by battery_level asc."""
        rows = [
            _lb("s.b", "B", battery_numeric=None, battery_display="low"),
            _lb("s.a", "A", battery_numeric=10.0, battery_display="10%"),
        ]
        result = sort_low_battery_rows(rows, SORT_FIELD_BATTERY_LEVEL, SORT_DIR_ASC)
        assert result[0].battery_numeric == 10.0
        assert result[1].battery_numeric is None

    def test_stable_tiebreaker(self):
        """Rows with same sort key should use friendly_name then entity_id as tiebreaker."""
        rows = [
            _lb("s.z", "Same", battery_numeric=10.0, battery_display="10%"),
            _lb("s.a", "Same", battery_numeric=10.0, battery_display="10%"),
        ]
        result = sort_low_battery_rows(rows, SORT_FIELD_BATTERY_LEVEL, SORT_DIR_ASC)
        # Tie-break by entity_id: s.a < s.z
        assert result[0].entity_id == "s.a"
        assert result[1].entity_id == "s.z"


# ── sort_unavailable_rows ─────────────────────────────────────────────────────

def _uv(entity_id, friendly_name, area=None, manufacturer=None):
    return UnavailableRow(entity_id=entity_id, friendly_name=friendly_name, area=area, manufacturer=manufacturer)


class TestSortUnavailableRows:
    def test_sort_by_friendly_name_asc(self):
        rows = [_uv("u.b", "Zebra"), _uv("u.a", "Apple")]
        result = sort_unavailable_rows(rows, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_ASC)
        assert result[0].friendly_name == "Apple"

    def test_sort_by_friendly_name_desc(self):
        rows = [_uv("u.b", "Zebra"), _uv("u.a", "Apple")]
        result = sort_unavailable_rows(rows, SORT_FIELD_FRIENDLY_NAME, SORT_DIR_DESC)
        assert result[0].friendly_name == "Zebra"

    def test_sort_by_area(self):
        rows = [_uv("u.b", "B", area="Kitchen"), _uv("u.a", "A", area="Attic")]
        result = sort_unavailable_rows(rows, "area", SORT_DIR_ASC)
        assert result[0].area == "Attic"
