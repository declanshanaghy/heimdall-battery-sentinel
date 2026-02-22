# 4.3 Infinite Scroll Feature

Status: review
<!-- NOTE: Status values MUST match sprint-status.yaml exactly: backlog | ready-for-dev | in-progress | review | done -->

## Story

As a Home Assistant user,
I want to see infinite scroll functionality in the battery history view,
So that I can seamlessly load more data as I scroll down without pagination.

## Acceptance Criteria

1. [x] Loads additional records when user scrolls within 200px of bottom
2. [x] Displays loading spinner during fetch
3. [x] Maintains scroll position after new records load
4. [x] Handles API errors gracefully
5. [x] Displays 'No more records' message when end reached

## Tasks / Subtasks

- [x] Update Intersection Observer threshold from 100px to 200px (AC: #1)
  - [x] Change rootMargin from '100px' to '200px' in panel-heimdall.js
- [x] Improve error handling for API failures (AC: #4)
  - [x] Add user-visible error message on API failure
- [x] Add tests for infinite scroll behavior
  - [x] Add unit test for IntersectionObserver configuration
  - [x] Add test for error handling

## Dev Notes

### Architecture Requirements
- Use Intersection Observer API for scroll detection ([Source: Implementation Notes])
- Throttle API calls to prevent excessive requests ([Source: Implementation Notes])
- Cache loaded pages to minimize redundant fetches ([Source: Implementation Notes])

### Technical Specifications
- Change rootMargin from '100px' to '200px' to meet AC #1
- Add error toast/banner for graceful API error handling
- Keep existing pagination infrastructure (page_size: 100)

### File Structure
1. `custom_components/heimdall_battery_sentinel/www/panel-heimdall.js`:
   - Update IntersectionObserver rootMargin to 200px
   - Add user-visible error handling

### Testing Requirements
- Unit test for IntersectionObserver rootMargin value
- Integration test for error handling path

## Dev Agent Record

### Agent Model Used
minimax-minimax-m2.5

### Debug Log References
N/A - No issues encountered

### Completion Notes List
- Updated IntersectionObserver rootMargin from '100px' to '200px' to meet AC #1
- Added user-visible error message in _loadPage error handler
- All 106 tests pass including 2 new tests for infinite scroll

### File List

| File | Action | Description |
|------|--------|-------------|
| `custom_components/heimdall_battery_sentinel/www/panel-heimdall.js` | Modify | Updated rootMargin to 200px, added user-visible error handling |
| `tests/test_infinite_scroll.py` | Create | New test file for infinite scroll behavior |

## Change Log
- 2026-02-21: Story created from Epic 4
- 2026-02-22: Story implementation completed - Updated IntersectionObserver threshold and error handling