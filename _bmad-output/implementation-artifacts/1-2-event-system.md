# Event System Implementation Story (1-2)

## Metadata
- **Id:** 1-2
- **Size:** 1 day
- **Epic:** Core Integration Setup (Epic 1)
- **Status:** in-progress

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
2. [ ] Add HA event listener for state_changed events in __init__.py
3. [ ] Add HA event listener for registry updates (entity/device/area)
4. [ ] Create event handler to process state changes and update store
5. [ ] Connect store notifications to WebSocket subscribers for real-time push
6. [ ] Add tests for event subscription functionality
7. [ ] Run full test suite and ensure no regressions
8. [ ] Update story status to review

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

## Implementation Steps (Deprecated - see Tasks)
1. Created `EventProducer` service with:
   - AMQP connection pooling
   - JSON schema validation
   - Retry logic (3 attempts with backoff)

2. Implemented `EventConsumer` with:
   - Dead letter queue handling
   - Circuit breaker pattern
   - Audit logging integration

## Dev Agent Record

### Agent Model Used
openrouter/minimax/minimax-m2.5

### Debug Log References
N/A - No issues encountered

### Completion Notes List
- (To be populated)

## Change Log
- 2026-02-21: Story implementation started - Implementing HA event subscriptions

## File List

| File | Action | Description |
|------|--------|-------------|
| `custom_components/heimdall_battery_sentinel/__init__.py` | Modify | Add HA event listeners |

## Status
in-progress

