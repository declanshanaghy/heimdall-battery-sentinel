"""Battery evaluation logic for Heimdall Battery Sentinel."""

from datetime import datetime
from typing import TypeVar

from .const import SEVERITY_ORANGE, SEVERITY_RED, SEVERITY_YELLOW
from .models import Severity

T = TypeVar("T")


def evaluate_numeric_battery(state: str, unit: str | None, threshold: int) -> tuple[bool, float | None, Severity | None]:
    """
    Evaluate numeric battery state.
    
    Returns: (is_low, numeric_value, severity)
    """
    if unit != "%":
        return False, None, None
    
    try:
        value = float(state)
    except (ValueError, TypeError):
        return False, None, None
    
    is_low = value <= threshold
    
    if not is_low:
        severity = None
    elif value <= 10:
        severity = Severity(SEVERITY_RED)
    elif value <= 20:
        severity = Severity(SEVERITY_ORANGE)
    else:
        severity = Severity(SEVERITY_YELLOW)
    
    return is_low, value, severity


def evaluate_textual_battery(state: str) -> tuple[bool, str]:
    """
    Evaluate textual battery state.
    
    Returns: (is_low, display_value)
    Only 'low' state is considered low. 'medium' and 'high' are excluded.
    """
    state_lower = state.lower().strip() if state else ""
    
    if state_lower not in ("low", "medium", "high"):
        return False, ""
    
    is_low = state_lower == "low"
    
    # Only return display value for 'low', exclude medium/high
    if is_low:
        return True, state_lower
    return False, ""


def evaluate_battery(state: str, unit: str | None, threshold: int) -> dict:
    """
    Evaluate battery state and return comprehensive result.
    
    Returns dict with:
    - is_low: bool
    - display: str
    - numeric: float | None
    - severity: Severity | None
    """
    is_low, numeric, severity = evaluate_numeric_battery(state, unit, threshold)
    
    if is_low:
        return {
            "is_low": True,
            "display": f"{round(numeric)}%" if numeric is not None else "",
            "numeric": numeric,
            "severity": severity,
        }
    
    is_low_text, display_text = evaluate_textual_battery(state)
    
    if is_low_text:
        # Textual 'low' gets the most critical severity (RED) since it's the lowest textual state
        # Also assign numeric=0 for proper sorting (lowest possible value)
        return {
            "is_low": True,
            "display": display_text,
            "numeric": 0,  # Sort as lowest possible value
            "severity": Severity(SEVERITY_RED),  # Most critical severity for textual 'low'
        }
    
    return {
        "is_low": False,
        "display": "",
        "numeric": None,
        "severity": None,
    }


def calculate_severity(numeric_value: float) -> Severity:
    """Calculate severity based on numeric battery value."""
    if numeric_value <= 10:
        return Severity(SEVERITY_RED)
    elif numeric_value <= 20:
        return Severity(SEVERITY_ORANGE)
    else:
        return Severity(SEVERITY_YELLOW)
