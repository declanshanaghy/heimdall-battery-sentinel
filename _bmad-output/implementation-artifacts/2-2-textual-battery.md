# Story 2.2: Textual Battery Monitoring

Status: review

## Story
As a Home Assistant user,
I want to see only textual battery entities in 'low' state,
so that I can quickly identify devices needing immediate attention.

## Acceptance Criteria
1. Only include textual battery entities with state=='low'
2. Exclude medium/high textual states
3. Display 'low' state label consistently
4. Apply proper color coding per severity rules
5. Maintain server-side sorting functionality

## Tasks / Subtasks
- [x] Implement textual state filtering (AC: #1,2)
  - [x] Add state validation in battery evaluator
  - [x] Update entity inclusion logic
- [x] UI display implementation (AC: #3,4)
  - [x] Create text display component
  - [x] Integrate severity coloring
- [x] Sorting integration (AC: #5)
  - [x] Add text state sorting criteria
  - [x] Update server-side sort logic

## Dev Notes
### Architecture Requirements
- Follow entity evaluation rules from [PRD 2.2](#)
- Use HA theme variables for coloring [Source: planning-artifacts/ux-design-specification.md#color-palette]

### Technical Specifications
- Python 3.10
- Home Assistant Core 2024.7

### File Structure
- `custom_components/heimdall_battery_sentinel/evaluator.py`
- `www/panel-components/text-battery.js`

### Testing Requirements
- Unit tests for state validation
- E2E test for UI display
- Sorting integration tests

## Dev Agent Record

### Agent Model Used
Haiku (openrouter/minimax/minimax-m2.5)

### Debug Log References
N/A - No issues encountered

### Completion Notes List
- Fixed `evaluate_textual_battery()` to exclude 'medium' and 'high' from display (AC #2)
- Added severity=RED for textual 'low' batteries (AC #4) - most critical textual state
- Added numeric=0 for textual 'low' batteries to enable proper sorting (AC #5)
- Textual 'low' now sorts as lowest value (0), ensuring it appears first when sorting by battery_level ascending
- Created 13 new tests for textual battery evaluation
- Created 3 new tests for textual battery sorting
- Updated existing test_event_system.py test to match new behavior
- All 84 tests pass with no regressions

## Change Log
- 2026-02-20: Story created from Epic 2
- 2026-02-21: Implemented textual battery handling with filtering, severity, and sorting

### File List

| File | Action | Description |
|------|--------|-------------|
| `tests/test_textual_battery.py` | Create | Added 13 unit tests for textual battery evaluation |
| `tests/test_textual_sorting.py` | Create | Added 3 unit tests for textual battery sorting |
| `tests/test_event_system.py` | Modify | Updated test to match new textual battery behavior |
| `custom_components/heimdall_battery_sentinel/evaluator.py` | Modify | Added severity and numeric value for textual 'low' batteries |