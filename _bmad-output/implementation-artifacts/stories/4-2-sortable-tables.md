# 4.2 Sortable Tables

## Background
Requirement 4.2 from PLANNING_ARTIFACTS/requirements.md specifies implementing client-side sorting for battery data tables to enable faster analysis without server roundtrips.

## User Story
As a field technician
I want to sort battery tables by different columns
So I can quickly identify patterns in performance data

## Acceptance Criteria
- [ ] Clicking column headers toggles ascending/descending sort
- [ ] Sort indicators show current sort state
- [ ] Handles numeric (capacity, voltage) and date (last_checked) columns
- [ ] Preserves sort state during pagination

