# Story: Project Structure Setup

## Metadata
- **Id:** 1-1
- **Size:** 1 day
- **Epic:** Core Integration Setup (Epic 1)
- **Status:** ready-for-dev

## Description
Initialize the integration structure following Home Assistant custom integration patterns. Creates the foundational project structure with all required directories, files, and configurations to support the battery monitoring and unavailable tracking features.

## Acceptance Criteria
Given an empty HA custom_components directory,  
When the integration is installed,  
Then it should appear in HA with the domain `heimdall_battery_sentinel`,  
And the structure should match the architecture document.  
Source: epics.md#1.1: Project Structure Setup

## Tasks
1. Create the base directory structure under `custom_components/heimdall_battery_sentinel/`
2. Implement `__init__.py` with basic integration setup
3. Create `manifest.json` with integration metadata
4. Implement `const.py` for domain constants
5. Create frontend directory structure for the custom panel
6. Set up minimal configuration flow
7. Create empty files for future components
8. Add basic logging setup

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