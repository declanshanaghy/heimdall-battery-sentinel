# Story: Project Structure Setup

## Metadata
- **Id:** 1-1
- **Size:** 1 day
- **Epic:** Core Integration Setup (Epic 1)
- **Status:** in-progress

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
anthropic/claude-sonnet-4-6

### Debug Log References
- CRIT-6: Fixed by stubbing `ConfigFlow.__init_subclass__` to accept `domain=` keyword
- CRIT-5: Misleading sensor state assertions replaced with real integration and unit tests
- All CRITICAL and HIGH review items from code-review.md addressed

### Completion Notes List
- **CRIT-1 → models.py**: Implemented `LowBatteryRow`, `UnavailableRow`, `compute_severity`, `sort_low_battery_rows`, `sort_unavailable_rows` with full type hints and serialization
- **CRIT-2 → evaluator.py**: Implemented `BatteryEvaluator` class + standalone `evaluate_battery_state`/`evaluate_unavailable_state` per ADR-005 rules (numeric % only, textual low only)
- **CRIT-3 → registry.py**: Implemented `MetadataResolver` with HA entity/device/area registry lookup, caching, and invalidation
- **CRIT-4 → websocket.py**: Implemented `heimdall/summary`, `heimdall/list`, `heimdall/subscribe` commands with voluptuous schema validation
- **CRIT-5 → tests/**: Replaced misleading test assertions with 97 real unit/integration tests covering models, evaluator, store, and integration setup
- **CRIT-6 → __init__.py**: Added `async_setup_entry`, `async_unload_entry`, `hass.data[DOMAIN]` initialization, state_changed event subscription, initial dataset population
- **HIGH-1 → store.py**: Implemented `HeimdallStore` with in-memory datasets, dataset versioning (ADR-008), pagination, and subscriber push model
- **HIGH-2 → config_flow.py**: Added full input validation with voluptuous schema, threshold range enforcement (5–100, step 5), options flow for post-setup changes (ADR-007)
- **HIGH-3 → __init__.py**: `async_setup_entry` + `async_unload_entry` + options update listener
- **HIGH-4 → www/panel-heimdall.js**: Implemented full ES module panel with tabs, sortable table, infinite scroll, WebSocket client (summary/list/subscribe), event handling, and shadow DOM
- **HIGH-5 → const.py**: Added all missing constants: `CONF_BATTERY_THRESHOLD`, `CONF_SCAN_INTERVAL`, `DEFAULT_THRESHOLD`, severity constants, WS command names, sort fields, tab names, storage keys
- **HIGH-6**: All story tasks now backed by actual implementation and passing tests
- **Tests**: 97 unit tests added across `test_models.py`, `test_evaluator.py`, `test_store.py`, and updated `test_integration_setup.py`; `conftest.py` provides HA stubs for offline testing
- **pytest.ini**: Added to configure test discovery and asyncio mode
- **Build**: 97/97 tests pass; no regressions

### File List

| File | Action | Description |
|------|--------|-------------|
| `custom_components/heimdall_battery_sentinel/__init__.py` | Modify | Added `async_setup_entry`, `async_unload_entry`, `hass.data[DOMAIN]` init, event subscriptions, initial dataset population |
| `custom_components/heimdall_battery_sentinel/const.py` | Modify | Added all missing constants: config keys, defaults, severity levels, WS commands, sort fields, tab names, storage keys |
| `custom_components/heimdall_battery_sentinel/models.py` | Implement | `LowBatteryRow`, `UnavailableRow`, `compute_severity`, `sort_low_battery_rows`, `sort_unavailable_rows` |
| `custom_components/heimdall_battery_sentinel/evaluator.py` | Implement | `BatteryEvaluator`, `evaluate_battery_state`, `evaluate_unavailable_state` per ADR-005 |
| `custom_components/heimdall_battery_sentinel/store.py` | Implement | `HeimdallStore` with dataset versioning, CRUD, pagination, subscriber push (ADR-008) |
| `custom_components/heimdall_battery_sentinel/registry.py` | Implement | `MetadataResolver` with HA entity/device/area registry lookup and caching (ADR-006) |
| `custom_components/heimdall_battery_sentinel/websocket.py` | Implement | WebSocket commands: `heimdall/summary`, `heimdall/list`, `heimdall/subscribe` (ADR-003) |
| `custom_components/heimdall_battery_sentinel/config_flow.py` | Modify | Full input validation, threshold enforcement, `HeimdallOptionsFlow` for ADR-007 |
| `custom_components/heimdall_battery_sentinel/www/panel-heimdall.js` | Implement | Full ES module: shadow DOM panel, tabs, sortable table, infinite scroll, WebSocket client |
| `tests/conftest.py` | Create | HA stub modules for offline unit testing; `mock_hass` and `mock_state` fixtures |
| `tests/test_integration_setup.py` | Modify | Replaced misleading sensor state assertions with real tests for domain, constants, module importability |
| `tests/test_models.py` | Create | 30 unit tests for models, severity, sorting |
| `tests/test_evaluator.py` | Create | 34 unit tests for battery evaluation rules (ADR-005) |
| `tests/test_store.py` | Create | 30 unit tests for store CRUD, pagination, versioning, subscribers |
| `pytest.ini` | Create | pytest configuration: testpaths, asyncio_mode |

## Change Log
- 2026-02-20: Initial story implementation (skeleton only) — CHANGES_REQUESTED
- 2026-02-20: Review follow-ups addressed — all CRITICAL and HIGH issues resolved; 97 tests pass
- 2026-02-20: Story Acceptance — CHANGES_REQUESTED (2 blocking items from code review)
