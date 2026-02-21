# 4.2 Sortable Tables

Status: in-progress

## Background
Requirement 4.2 from PLANNING_ARTIFACTS/requirements.md specifies implementing client-side sorting for battery data tables to enable faster analysis without server roundtrips.

## User Story
As a field technician
I want to sort battery tables by different columns
So I can quickly identify patterns in performance data

## Acceptance Criteria
- [x] Clicking column headers toggles ascending/descending sort
- [x] Sort indicators show current sort state
- [x] Handles numeric (capacity, voltage) and date (last_checked) columns
- [x] Preserves sort state during pagination

## Dev Notes
All ACs already implemented in panel-heimdall.js:
- _onSortClick() handles toggle logic
- ▲/▼ icons show sort direction
- Backend receives sort params via WebSocket
- _sort state preserved across pagination

