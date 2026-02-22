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
    """
    state_lower = state.lower().strip() if state else ""
    
    if state_lower not in ("low", "medium", "high"):
        return False, ""
    
    is_low = state_lower == "low"
    display_value = state_lower
    
    return is_low, display_value


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
        return {
            "is_low": True,
            "display": display_text,
            "numeric": None,
            "severity": None,
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
