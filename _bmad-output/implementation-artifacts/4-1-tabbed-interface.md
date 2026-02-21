# Story 4.1: Tabbed Interface

Status: ready-for-dev
<!-- NOTE: Status values MUST match sprint-status.yaml exactly: backlog | ready-for-dev | in-progress | review | done -->

## Story

As a Home Assistant user,
I want to see two separate tabs for Low Battery and Unavailable entities,
so that I can quickly switch between these views with live updating counts.

## Acceptance Criteria

1. Given the panel is open, when viewing the interface, then it should show two tabs labeled "Low Battery" and "Unavailable" with live counts that update in real-time
2. Given the tabs are visible, when clicking on a tab, then it should switch to that view instantly with visual feedback (underline/color change)
3. Given the tab is switched, when viewing, then it should maintain the correct tab selection across panel reloads

## Tasks / Subtasks

- [ ] Implement tab component (AC: #1, #2)
  - [ ] Create tab bar UI with two tabs
  - [ ] Implement tab switching logic
  - [ ] Add live count badges that update from backend
- [ ] Persist tab state (AC: #3)
  - [ ] Store selected tab in local storage
  - [ ] Restore tab selection on panel load

## Dev Notes

### Architecture Requirements
- Tab component must use HA-native patterns ([Source: planning-artifacts/architecture.md#ADR-001])
- Live counts must come via websocket subscriptions ([Source: planning-artifacts/architecture.md#ADR-003])
- UI must be responsive and work on mobile ([Source: planning-artifacts/prd.md#FR-UI-004])

### Technical Specifications
- Use `<ha-tabs>` component from HA frontend
- Implement with Vanilla JS (no Lit)
- Live counts should update within 500ms of backend changes

### File Structure
1. `custom_components/heimdall_battery_sentinel/www/panel-heimdall.js`:
   - Tab component implementation
   - State management
2. `custom_components/heimdall_battery_sentinel/__init__.py`:
   - Add websocket handlers for count updates

### Testing Requirements
- Unit tests for tab persistence
- Integration test for live count updates
- Visual regression test for tab states

### UX Flow Diagram
```mermaid
stateDiagram-v2
    [*] --> LowBatteryTab
    LowBatteryTab --> UnavailableTab: Click Unavailable tab
    UnavailableTab --> LowBatteryTab: Click Low Battery tab
    LowBatteryTab --> LowBatteryTab: Count updates
    UnavailableTab --> UnavailableTab: Count updates
```

### References
- [Source: planning-artifacts/epics.md#4.1-Tabbed-Interface]
- [Source: planning-artifacts/architecture.md#ADR-003]
- [Source: planning-artifacts/prd.md#FR-UI-003]

## Dev Agent Record

### Agent Model Used
TBD

### Debug Log References
TBD

### Completion Notes List
TBD

### File List

| File | Action | Description |
|------|--------|-------------|
| TBD | | |

## Change Log
- 2026-02-20: Story created from Epic 4