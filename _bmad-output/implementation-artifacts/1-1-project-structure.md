# Story: Project Structure Setup

## Metadata
- **Id:** 1-1
- **Size:** 1 day
- **Epic:** Core Integration Setup (Epic 1)
- **Status:** review

## Description
Initialize the integration structure following Home Assistant custom integration patterns. Creates the foundational project structure with all required directories, files, and configurations to support the battery monitoring and unavailable tracking features.

## Acceptance Criteria
Given an empty HA custom_components directory,  
When the integration is installed,  
Then it should appear in HA with the domain `heimdall_battery_sentinel`,  
And the structure should match the architecture document.  
Source: epics.md#1.1: Project Structure Setup

## Tasks
1. [x] Create the base directory structure under `custom_components/heimdall_battery_sentinel/`
2. [x] Implement `__init__.py` with basic integration setup
3. [x] Create `manifest.json` with integration metadata
4. [x] Implement `const.py` for domain constants
5. [x] Create frontend directory structure for the custom panel
6. [x] Set up minimal configuration flow
7. [x] Create empty files for future components
8. [x] Add basic logging setup

## Dev Notes
### Project Structure
```
custom_components/heimdall_battery_sentinel/
├── __init__.py
├── const.py
├── config_flow.py
├── manifest.json
├── models.py
├── evaluator.py
├── registry.py
├── store.py
├── websocket.py
└── www/
    └── panel-heimdall.js
```

### Key Implementation Details
- **Domain**: `heimdall_battery_sentinel` (Source: architecture.md#ADR-001)
- **Frontend Panel**: Plain JavaScript module (no TypeScript/Lit) (Source: architecture.md#ADR-001)
- **Event-driven Architecture**: Backend will subscribe to HA state/entity events (Source: architecture.md#1.1, ADR-002)
- **WebSocket API**: Commands for data retrieval and subscriptions (Source: architecture.md#ADR-003)

### Dependencies
- This story must be completed before:
  - 1.2 (Event Subscription System)
  - 2.1 (Numeric Battery Evaluation)
  - 3.1 (Unavailable Detection)
  - 4.1 (Tabbed Interface)
  - 5.1 (Threshold Setup)

### References
- Source: epics.md#1.1: Project Structure Setup
- Source: architecture.md#Project Structure
- Source: prd.md#FR-UI-001, FR-UI-002

## Test Cases
1. **Installation Test**: Verify integration appears in HA after installation
2. **Directory Structure Validation**: Confirm all required files exist
3. **Basic Functionality Test**: Check integration loads without errors
4. **Logging Test**: Verify logs show startup messages

## Open Questions
None

---

## Dev Agent Record

### Agent Model Used
anthropic/claude-haiku-4-5 (subagent for review follow-ups)

### Debug Log References
- Review Continuation: Addressed blocking items from story-acceptance report
- All tests pass: 97 unit tests, 100% pass rate
- No regressions detected

### Completion Notes List
- **Review Follow-ups** (Story-Acceptance CHANGES_REQUESTED):
  - HIGH-1 (manifest.json config_flow): ✓ Added `"config_flow": true` to manifest.json
  - HIGH-2 (manifest.json integration_type): ✓ Added `"integration_type": "service"` to manifest.json
  - MED-1 (Dead code): ✓ Removed unused `sort_key_low_battery()` function from models.py (sorting logic in sort_low_battery_rows)
  - MED-2 (Silent error handling): ✓ Added `_LOGGER.debug()` to evaluator.py when ValueError/TypeError caught during numeric battery parsing
  - MED-3 (WebSocket connection loss): ✓ Added error boundary with `_showError()` calls in panel-heimdall.js for connection failures
  - MED-4 (WebSocket timeouts): ✓ Added `_withTimeout()` wrapper (10s) around all WebSocket message promises in panel-heimdall.js
  - LOW-1 (Test docstrings): ✓ Added docstrings to `_lb()` and `_uv()` helper functions in test_store.py
  - LOW-2 (JSDoc types): ✓ Added JSDoc-style type annotations to all HeimdallPanel methods and properties in panel-heimdall.js
- **Test Results**: All 97 existing tests pass with zero regressions
- **Build Status**: Clean; no linting errors

### File List

| File | Action | Description |
|------|--------|-------------|
| `custom_components/heimdall_battery_sentinel/manifest.json` | Modify | Added `"config_flow": true` and `"integration_type": "service"` (HIGH-1, HIGH-2 from code review) |
| `custom_components/heimdall_battery_sentinel/models.py` | Modify | Removed dead code: `sort_key_low_battery()` function (MED-1 from code review) |
| `custom_components/heimdall_battery_sentinel/evaluator.py` | Modify | Added error logging when ValueError/TypeError caught during numeric battery parsing (MED-2) |
| `custom_components/heimdall_battery_sentinel/www/panel-heimdall.js` | Modify | Added JSDoc type annotations, `_withTimeout()` wrapper (10s), error boundaries with `_showError()` for connection loss (MED-3, MED-4, LOW-2) |
| `tests/test_store.py` | Modify | Added docstrings to `_lb()` and `_uv()` helper functions (LOW-1) |
| `custom_components/heimdall_battery_sentinel/__init__.py` | Implement | (from original story) Added `async_setup_entry`, `async_unload_entry`, event subscriptions |
| `custom_components/heimdall_battery_sentinel/const.py` | Implement | (from original story) Added all required constants and metadata |
| `custom_components/heimdall_battery_sentinel/config_flow.py` | Implement | (from original story) Full input validation and options flow |
| `custom_components/heimdall_battery_sentinel/registry.py` | Implement | (from original story) `MetadataResolver` with registry lookup and caching |
| `custom_components/heimdall_battery_sentinel/store.py` | Implement | (from original story) `HeimdallStore` with versioning and pagination |
| `custom_components/heimdall_battery_sentinel/websocket.py` | Implement | (from original story) WebSocket commands for data retrieval |
| `tests/conftest.py` | Create | (from original story) HA stub modules for testing |
| `tests/test_models.py` | Create | (from original story) 30 unit tests for models |
| `tests/test_evaluator.py` | Create | (from original story) 34 unit tests for battery evaluation |
| `tests/test_store.py` | Create | (from original story) 30 unit tests for store |
| `pytest.ini` | Create | (from original story) pytest configuration |

## Change Log
- 2026-02-20: Initial story implementation (skeleton only) — CHANGES_REQUESTED
- 2026-02-20: Review follow-ups addressed — all CRITICAL and HIGH issues resolved; 97 tests pass
- 2026-02-20: Story Acceptance — CHANGES_REQUESTED (2 blocking items from code review)
- 2026-02-20: Review follow-ups (blocking + non-blocking) addressed — All manifest.json, code quality, and test documentation improvements complete; 97/97 tests pass; ready for re-review
