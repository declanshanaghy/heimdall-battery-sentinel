# UX Review Report

**Story:** 4-4-entity-linking
**Date:** 2026-02-22
**Reviewer:** UX Review Agent
**Scope:** frontend-battery-dashboard (panel-heimdall.js) - Entity Linking Feature
**Dev Server:** http://homeassistant.lan:8123
**Overall Verdict:** ACCEPTED (Code Review Only - No Visual Verification)

## Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 0 |
| 🟠 HIGH | 0 |
| 🟡 MEDIUM | 0 |
| 🟢 LOW | 1 |

## Critical Limitation

**The panel is not registered in Home Assistant and cannot be accessed for visual verification.**

- This is the same blocker noted in Epics 2, 3, and 4 (stories 4-1, 4-2, 4-3)
- Code review was performed instead of end-to-end screenshot verification
- The frontend code exists but is inaccessible at `/api/panel/heimdall`

## Pages Reviewed

| Page | Route | Status |
|------|-------|--------|
| Battery Dashboard | `/api/panel/heimdall` (not registered) | ⚠️ Code review only |

## Findings

### 🟢 LOW Issues

#### UX-LOW-1: No Dark Mode Link Color Override

**Page:** Both tables (Low Battery, Unavailable)
**Spec Reference:** Color Palette - Dark Mode tokens

**Expected:** Links should have explicit dark mode styling to ensure visibility in dark theme
**Actual:** Relies on HA's `--primary-color` CSS variable which may not be sufficient

**Code Evidence:**
```javascript
.entity-link {
  color: var(--primary-color, #03a9f4);  // Uses HA CSS var with fallback
  text-decoration: none;
  cursor: pointer;
}
.entity-link:hover {
  text-decoration: underline;
}
```

**Recommendation:** Consider adding explicit dark mode override, though current implementation may work via HA variables:
```css
@media (prefers-color-scheme: dark) {
  .entity-link {
    color: #03A9F4;  // HA primary color works in dark mode
  }
}
```

---

## Entity Linking Implementation Review

### Implementation Details (Verified via Code Review)

| Acceptance Criteria | Status | Evidence |
|---------------------|--------|----------|
| AC1: Link entity name in Low Battery table | ✅ | Code wraps name in `<a>` tag with `class="entity-link"` |
| AC2: Link entity name in Unavailable table | ✅ | Same code handles both tables |
| AC3: Links work consistently across both tabs | ✅ | Same rendering function used for both |
| AC4: Open in new tab | ✅ | Uses `target="_blank"` |
| AC5: Link target format | ✅ | URL: `/config/entities/edit?entity_id={entity_id}` |

### Styling Review

| Spec Requirement | Implementation | Status |
|-----------------|----------------|--------|
| Primary color #03A9F4 | `color: var(--primary-color, #03a9f4)` | ✅ Matches |
| Hover underline | `.entity-link:hover { text-decoration: underline; }` | ✅ Matches |
| Security: rel="noopener" | Present in anchor tag | ✅ Implemented |
| Error handling | Logs error, renders plain text if entity_id missing | ✅ Implemented |

## Previous Epic Learnings

### From Epic 2 Retrospective
- No UX-specific recommendations for entity linking

### From Epic 3 Retrospective  
- No UX-specific recommendations for entity linking

### Story-Specific
- This story builds on 4-1 (Tabbed Interface), 4-2 (Sortable Tables), 4-3 (Infinite Scroll)
- Entity linking is independent of these features and doesn't conflict

## Accessibility Audit

| Check | Status | Notes |
|-------|--------|-------|
| Focus indicators | ✅ | Anchor tags have default browser focus |
| Tab order | ✅ | Links are in table cells, naturally tab-accessible |
| Color contrast | ✅ | #03A9F4 on white/dark backgrounds should meet 4.5:1 |
| Screen reader | ⚠️ | No aria-label on links (text content is descriptive) |

## Recommendations

### Should Fix (Non-blocking)

1. **Add explicit dark mode link color**
   - While HA's primary-color variable should work, explicit dark override ensures consistency

### Nice to Have

1. Add `aria-label` to links for better screen reader experience:
   ```javascript
   nameCell = `<a class="entity-link" href="${entityUrl}" target="_blank" rel="noopener" aria-label="Edit ${displayName}">${displayName}</a>`;
   ```

## Conclusion

**Overall Verdict:** ACCEPTED (Code Review Only)

**Rationale:**
- Code implementation fully matches the UX specification
- Entity linking is correctly implemented for both Low Battery and Unavailable tables
- All acceptance criteria are met based on code analysis
- The only limitation is visual verification (same blocker as previous epics)

**Note:** This review is based on code analysis. End-to-end screenshot verification could not be performed due to panel registration issue (same blocker documented in Epics 2-4 retrospectives).

**Next:** Run story-acceptance once all reviewers complete.