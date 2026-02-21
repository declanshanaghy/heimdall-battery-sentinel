"""Battery evaluation logic for heimdall_battery_sentinel."""
from __future__ import annotations

import logging
from typing import Optional

from .const import (
    DEVICE_CLASS_BATTERY,
    STATE_LOW,
    STATE_UNAVAILABLE,
    TEXTUAL_BATTERY_STATES,
    UNIT_PERCENT,
)
from .models import LowBatteryRow, UnavailableRow, compute_severity

_LOGGER = logging.getLogger(__name__)


def _get_friendly_name(state) -> str:
    """Extract friendly name from a HA state object."""
    if state.attributes and "friendly_name" in state.attributes:
        return state.attributes["friendly_name"]
    return state.entity_id


def _get_device_class(state) -> Optional[str]:
    """Extract device_class from a HA state object's attributes."""
    if state.attributes:
        return state.attributes.get("device_class")
    return None


def _get_unit(state) -> Optional[str]:
    """Extract unit_of_measurement from a HA state object's attributes."""
    if state.attributes:
        return state.attributes.get("unit_of_measurement")
    return None


def evaluate_battery_state(
    state,
    threshold: int,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    area: Optional[str] = None,
) -> Optional[LowBatteryRow]:
    """Evaluate a HA state object for low battery status.

    Rules (per ADR-005):
    - Numeric: accept only if device_class=battery, state is parseable as float,
      AND unit_of_measurement == "%". Include if battery_level <= threshold.
    - Textual: accept only if device_class=battery and state in {low, medium, high}
      (case-insensitive). Include only if state == "low".
    - Unavailable states are skipped here (handled by evaluate_unavailable).

    Args:
        state: Home Assistant State object.
        threshold: Battery percentage threshold (5–100).
        manufacturer: Pre-resolved manufacturer string or None.
        model: Pre-resolved model string or None.
        area: Pre-resolved area name or None.

    Returns:
        LowBatteryRow if entity qualifies as low battery, else None.
    """
    if state is None:
        return None

    device_class = _get_device_class(state)
    if device_class != DEVICE_CLASS_BATTERY:
        return None

    state_value = state.state
    if state_value is None or state_value == STATE_UNAVAILABLE:
        return None

    friendly_name = _get_friendly_name(state)

    # --- Try numeric battery ---
    unit = _get_unit(state)
    try:
        numeric_value = float(state_value)
        if unit == UNIT_PERCENT:
            if numeric_value <= threshold:
                severity = compute_severity(numeric_value)
                display = f"{round(numeric_value)}%"
                return LowBatteryRow(
                    entity_id=state.entity_id,
                    friendly_name=friendly_name,
                    battery_display=display,
                    battery_numeric=numeric_value,
                    severity=severity,
                    manufacturer=manufacturer,
                    model=model,
                    area=area,
                )
            # Numeric battery but above threshold — not low
            return None
        # Numeric but wrong unit — skip
        _LOGGER.debug(
            "Skipping entity %s: numeric battery but unit is %r, expected %r",
            state.entity_id,
            unit,
            UNIT_PERCENT,
        )
        return None
    except (ValueError, TypeError):
        pass

    # --- Try textual battery ---
    normalized = state_value.lower()
    if normalized in TEXTUAL_BATTERY_STATES:
        if normalized == STATE_LOW:
            return LowBatteryRow(
                entity_id=state.entity_id,
                friendly_name=friendly_name,
                battery_display=STATE_LOW,
                battery_numeric=None,
                severity=None,
                manufacturer=manufacturer,
                model=model,
                area=area,
            )
        # medium or high — not low
        return None

    _LOGGER.debug(
        "Entity %s: device_class=battery but state %r is not numeric%% or textual; skipping",
        state.entity_id,
        state_value,
    )
    return None


def evaluate_unavailable_state(
    state,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    area: Optional[str] = None,
) -> Optional[UnavailableRow]:
    """Evaluate a HA state object for unavailable status.

    Rule: state == "unavailable" (exact string, per ADR-005).

    Args:
        state: Home Assistant State object.
        manufacturer: Pre-resolved manufacturer string or None.
        model: Pre-resolved model string or None.
        area: Pre-resolved area name or None.

    Returns:
        UnavailableRow if entity is unavailable, else None.
    """
    if state is None:
        return None
    if state.state != STATE_UNAVAILABLE:
        return None

    friendly_name = _get_friendly_name(state)
    return UnavailableRow(
        entity_id=state.entity_id,
        friendly_name=friendly_name,
        manufacturer=manufacturer,
        model=model,
        area=area,
    )


class BatteryEvaluator:
    """Evaluates all HA states against battery and unavailable rules.

    Maintains a current threshold and provides batch evaluation helpers.
    """

    def __init__(self, threshold: int) -> None:
        """Initialize with a battery threshold.

        Args:
            threshold: Battery percentage threshold (5–100, step 5).
        """
        self._threshold = threshold

    @property
    def threshold(self) -> int:
        """Return current threshold."""
        return self._threshold

    @threshold.setter
    def threshold(self, value: int) -> None:
        """Update the threshold. Does not recompute cached rows."""
        self._threshold = value

    def evaluate_low_battery(
        self,
        state,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        area: Optional[str] = None,
    ) -> Optional[LowBatteryRow]:
        """Evaluate a single state for low battery.

        Args:
            state: Home Assistant State object.
            manufacturer: Resolved manufacturer or None.
            model: Resolved model or None.
            area: Resolved area name or None.

        Returns:
            LowBatteryRow if qualifies, else None.
        """
        return evaluate_battery_state(state, self._threshold, manufacturer, model, area)

    def evaluate_unavailable(
        self,
        state,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        area: Optional[str] = None,
    ) -> Optional[UnavailableRow]:
        """Evaluate a single state for unavailability.

        Args:
            state: Home Assistant State object.
            manufacturer: Resolved manufacturer or None.
            model: Resolved model or None.
            area: Resolved area name or None.

        Returns:
            UnavailableRow if qualifies, else None.
        """
        return evaluate_unavailable_state(state, manufacturer, model, area)

    def batch_evaluate(self, states, metadata_fn=None):
        """Evaluate a collection of HA states.

        Args:
            states: Iterable of HA State objects.
            metadata_fn: Optional callable(entity_id) -> (manufacturer, model, area).

        Returns:
            Tuple of (list[LowBatteryRow], list[UnavailableRow]).
        """
        low_battery: list[LowBatteryRow] = []
        unavailable: list[UnavailableRow] = []

        for state in states:
            if metadata_fn is not None:
                meta = metadata_fn(state.entity_id)
                manufacturer, model, area = meta if meta else (None, None, None)
            else:
                manufacturer, model, area = None, None, None

            lb_row = self.evaluate_low_battery(state, manufacturer, model, area)
            if lb_row is not None:
                low_battery.append(lb_row)

            un_row = self.evaluate_unavailable(state, manufacturer, model, area)
            if un_row is not None:
                unavailable.append(un_row)

        return low_battery, unavailable
