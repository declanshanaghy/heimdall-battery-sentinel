# Story 2.2: Textual Battery Monitoring

Status: ready-for-dev

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
- [ ] Implement textual state filtering (AC: #1,2)
  - [ ] Add state validation in battery evaluator
  - [ ] Update entity inclusion logic
- [ ] UI display implementation (AC: #3,4)
  - [ ] Create text display component
  - [ ] Integrate severity coloring
- [ ] Sorting integration (AC: #5)
  - [ ] Add text state sorting criteria
  - [ ] Update server-side sort logic

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
anthropic/claude-sonnet-4-6

## Change Log
- 2026-02-20: Story created from Epic 2