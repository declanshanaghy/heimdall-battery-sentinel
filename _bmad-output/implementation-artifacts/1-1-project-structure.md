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

## Dev Agent Record

### Agent Model Used
openrouter/minimax/minimax-m2.5

### Debug Log References
N/A - No issues encountered

### Completion Notes List
- Created full project structure following HA custom integration patterns
- All 8 tasks completed with 16 passing tests
- Implemented manifest.json with required HA metadata
- Created const.py with domain constants and default values
- Implemented __init__.py with async_setup_entry/unload_entry
- Created config_flow.py and options_flow.py for threshold configuration
- Created placeholder modules: models.py, evaluator.py, registry.py, store.py, websocket.py
- Created frontend panel in www/panel-heimdall.js with tabbed interface and infinite scroll
- Added logging throughout with _LOGGER

## Change Log
- 2026-02-21: Story implementation completed - Created full HA custom integration structure

## File List

| File | Action | Description |
|------|--------|-------------|
| `custom_components/heimdall_battery_sentinel/__init__.py` | Create | Integration entry point with setup/teardown |
| `custom_components/heimdall_battery_sentinel/manifest.json` | Create | HA integration manifest with metadata |
| `custom_components/heimdall_battery_sentinel/const.py` | Create | Domain constants, defaults, WS commands |
| `custom_components/heimdall_battery_sentinel/config_flow.py` | Create | Config flow for initial threshold setup |
| `custom_components/heimdall_battery_sentinel/options_flow.py` | Create | Options flow for threshold configuration |
| `custom_components/heimdall_battery_sentinel/models.py` | Create | Data models for LowBatteryRow, UnavailableRow |
| `custom_components/heimdall_battery_sentinel/evaluator.py` | Create | Battery evaluation logic (numeric/textual) |
| `custom_components/heimdall_battery_sentinel/registry.py` | Create | Registry cache for metadata enrichment |
| `custom_components/heimdall_battery_sentinel/store.py` | Create | In-memory data store with subscription support |
| `custom_components/heimdall_battery_sentinel/websocket.py` | Create | WebSocket API commands (summary, list, subscribe) |
| `custom_components/heimdall_battery_sentinel/helpers.py` | Create | Helper functions for registry access |
| `custom_components/heimdall_battery_sentinel/www/panel-heimdall.js` | Create | Frontend panel with tabs and infinite scroll |
| `tests/test_project_structure.py` | Create | Project structure validation tests |
| `pyproject.toml` | Create | Python project configuration with pytest |

## Status
review