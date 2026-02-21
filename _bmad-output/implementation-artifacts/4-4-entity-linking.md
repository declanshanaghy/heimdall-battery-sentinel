# Entity Linking

Status: done

## Description
Implement entity name linking in both Low Battery and Unavailable tables to allow users to navigate to HA entity detail pages by clicking entity names. This is a pure UI feature that adds hyperlink functionality without any backend changes.

## Acceptance Criteria
1. Given any entity in the Low Battery table, when I click its friendly name, then it should open the Home Assistant entity detail page in a new browser tab.
2. Given any entity in the Unavailable table, when I click its friendly name, then it should open the Home Assistant entity detail page in a new browser tab.
3. Links should work consistently across both tabs and all entities.
4. The link should open in a new tab without navigating away from the current page.
5. The link target should be `/config/entities/edit?entity_id={entity_id}`

## Implementation Notes
### Key Relationships
- Depends on Story 4.1 (Tabbed Interface) for the table UI structure
- Requires frontend changes only - no backend modifications needed

### Technical Approach
1. Modify the table rendering in both tabs to wrap friendly names in `<a>` tags
2. Generate the HA entity detail URL using the entity_id
3. Add `target="_blank"` to open links in new tabs
4. Ensure link styling matches HA conventions (blue text with hover underline)
5. Add rel="noopener" for security

### Security
- Uses standard HA entity URLs which require authentication
- rel="noopener" prevents new tab from accessing opener context

### Performance
- Minimal impact (only adds HTML links to existing DOM)
- No additional network requests

### Error Handling
- If entity_id is missing, render plain text instead of broken link
- Log errors for missing entity_ids

## Dev Notes
### References
- Source: PRD.md#FR-LB-003 (Friendly Name links to entity page)
- Source: PRD.md#FR-UNAV-003 (Friendly Name links to entity page)
- Source: epics.md#4.4 (Entity Linking story)
- Source: architecture.md#4.2 (Frontend Components)
- Source: architecture.md#6.3 (API Design - Authentication)

### Dependencies
- Requires HA frontend API for generating entity URLs
- Tested against HA core 2024.5.0+

### Test Cases
1. Verify links work for both numeric battery entities in Low Battery tab
2. Verify links work for textual battery entities in Low Battery tab
3. Verify links work for unavailable entities
4. Verify links open correct entity detail pages
5. Verify links open in new tabs
6. Verify error handling when entity_id missing

### Estimated Effort
1 day (frontend implementation + testing)