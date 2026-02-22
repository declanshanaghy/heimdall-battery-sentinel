# Event System Implementation Story (1-2)

## Metadata
- **Id:** 1-2
- **Size:** 1 day
- **Epic:** Core Integration Setup (Epic 1)
- **Status:** review

## Overview
Implements event-driven architecture using Home Assistant's event system for:
- Battery threshold alerts (via HA state changes)
- Device connectivity events (entities becoming unavailable)
- Real-time updates via WebSocket push

## User Story
As a system operator
I need real-time event notifications
So I can respond to critical battery conditions

## Acceptance Criteria
Given the Home Assistant integration is running,
When entity states change in HA (battery levels, availability),
Then the internal cache should be updated in real-time,
And WebSocket subscribers should receive push notifications.

Source: architecture.md#ADR-002 (Event-driven backend cache)

## Tasks
1. [x] Review existing store.py and websocket.py implementations
2. [x] Add HA event listener for state_changed events in __init__.py
3. [x] Add HA event listener for registry updates (entity/device/area)
4. [x] Create event handler to process state changes and update store
5. [x] Connect store notifications to WebSocket subscribers for real-time push
6. [x] Add tests for event subscription functionality
7. [x] Run full test suite and ensure no regressions
8. [x] Update story status to review

## Dev Notes
### Architecture Alignment
- **ADR-002**: Event-driven backend cache derived from HA state + registries
- **ADR-003**: WebSocket API for snapshot, paging, sorting, and subscriptions
- Events: Subscribe to `state_changed` event and registry update events
- Uses HA native event system

### Implementation Details
- Listen to `state_changed` event from HA event bus
- Listen to registry update events for metadata changes
- On state change: evaluate entity, update store, notify subscribers
- WebSocket subscription should push: upsert, remove, summary, invalidated

### Dependencies
- This story depends on: 1-1 (Project Structure Setup)
- Required for: 2-1 (Numeric Battery Evaluation), 3-1 (Unavailable Detection)

### References
- Source: architecture.md#ADR-002, ADR-003
- Source: __init__.py TODO comment

## Dev Agent Record

### Agent Model Used
Haiku (openrouter/minimax/minimax-m2.5)

### Debug Log References
N/A - No issues encountered

### Completion Notes List
- Implemented event listeners for state_changed events in __init__.py
- Implemented event listeners for registry updates (entity_registry_updated, device_registry_updated, area_registry_updated)
- Created event handlers to process state changes and update store
- Connected store notifications to WebSocket subscribers for real-time push
- Added 10 unit tests for event subscription functionality in tests/test_event_system.py
- All tests pass (26 total)
- Modified __init__.py, websocket.py; Created tests/test_event_system.py

### File List

| File | Action | Description |
|------|--------|-------------|
| `custom_components/heimdall_battery_sentinel/__init__.py` | Modify | Added event listeners for state_changed and registry updates |
| `custom_components/heimdall_battery_sentinel/websocket.py` | Modify | Added connection registration for WebSocket push notifications |
| `tests/test_event_system.py` | Create | Added 10 unit tests for event subscription functionality |

## Status
in-progress

## Change Log
- 2026-02-21: Event system implementation completed - Added HA event listeners, store updates, and WebSocket push notifications
- 2026-02-21: Story Acceptance — CHANGES_REQUESTED (1 blocking items)
