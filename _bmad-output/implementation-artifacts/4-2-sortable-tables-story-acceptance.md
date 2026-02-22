# Story Acceptance Report

**Story:** 4-2-sortable-tables
**Date:** 2026-02-22
**Judge:** Story Acceptance Agent

## Overall Verdict: CHANGES_REQUESTED 🔄

The UX reviewer found a CRITICAL issue that blocks acceptance. The panel is not registered in Home Assistant, preventing end-to-end visual verification. All other acceptance criteria are met, but this blocking issue must be resolved before the story can be accepted.

## Review Summary

| Reviewer | Report | Overall Verdict | Blocking Items |
|----------|--------|-----------------|----------------|
| Code Review | [4-2-sortable-tables-code-review.md](4-2-sortable-tables-code-review.md) | ACCEPTED | 0 |
| QA Tester | [4-2-sortable-tables-qa-tester.md](4-2-sortable-tables-qa-tester.md) | NOT_REQUIRED | 0 |
| UX Review | [4-2-sortable-tables-ux-review.md](4-2-sortable-tables-ux-review.md) | CHANGES_REQUESTED | 1 |
| **Total blocking** | | | **1** |

## 🚫 Blocking Items (Must Fix)

### From UX Review

| ID | Severity | Finding | Reference |
|----|----------|---------|-----------|
| UX-CRIT-1 | CRITICAL | Panel Not Registered in Home Assistant | [UX-CRIT-1](4-2-sortable-tables-ux-review.md#critical-issues) |

**UX-CRIT-1 Details:**
The custom panel `/panel/heimdall` returns 404. The panel file exists at `custom_components/heimdall_battery_sentinel/www/panel-heimdall.js` but is not registered in Home Assistant configuration. This is a recurring blocker documented in Epics 2, 3, and 4.

**Root Cause:** The panel registration in `__init__.py` uses incorrect parameters:
```python
await hass.components.frontend.async_register_panel(
    "heimdall",
    "frontend",  # Incorrect - should be "javascript"
    "heimdall_battery_sentinel",  # JS module path doesn't exist
    None
)
```

## ℹ️ Non-Blocking Observations (Awareness Only)

These do not affect the decision. Address at developer discretion.

### Code Review (MEDIUM / LOW)
- MED-1: sprint-status.yaml modified but NOT in story's File List (minor docs drift)

### QA Tester (MEDIUM / LOW)
None

### UX Review (MEDIUM / LOW)
- UX-MED-1: Typography doesn't match token scale (h1 font-size: 24px should be 20px)
- UX-MED-2: No explicit dark mode overrides
- UX-LOW-1: Sort icons use Unicode arrows (↑↓) instead of HA icons
- UX-LOW-2: Threshold slider shows "(Coming soon)" - not functional

## Status Update

| Field | Before | After |
|-------|--------|-------|
| Story file status | review | in-progress |
| sprint-status.yaml | in-progress | in-progress |

## Acceptance Criteria Status

All acceptance criteria are implemented correctly:

| AC | Status | Evidence |
|----|--------|----------|
| AC1: Clicking column headers toggles ascending/descending sort | ✅ Verified | Code review confirms toggle logic in panel-heimdall.js |
| AC2: Sort indicators show current sort state | ✅ Verified | Sort icons (↑/↓) displayed based on sort state |
| AC3: Handles numeric (capacity, voltage) and date (last_checked) columns | ✅ Verified | Backend handles battery_level and updated_at; frontend uses toLocaleString() |
| AC4: Preserves sort state during pagination | ✅ Verified | Sort params sent in API request |

## Next Steps

1. Fix panel registration in `__init__.py` - use correct module type ("javascript" not "frontend")
2. Re-run dev-story to address the blocking panel registration issue
3. Re-run code-review / qa-tester / ux-review / story-acceptance
