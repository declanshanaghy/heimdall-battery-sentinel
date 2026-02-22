# UX Review Report

**Story:** 4-2-sortable-tables
**Date:** 2026-02-22
**Reviewer:** UX Review Agent
**Scope:** frontend-battery-dashboard (panel-heimdall.js)
**Dev Server:** http://homeassistant.lan:8123
**Overall Verdict:** CHANGES_REQUESTED

## Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 1 |
| 🟠 HIGH | 0 |
| 🟡 MEDIUM | 2 |
| 🟢 LOW | 2 |

## Previous Epic Learnings

Checked retrospective recommendations from Epics 2 & 3:
- Epic 3 retrospective: No specific UX recommendations
- Epic 2 retrospective: No specific UX recommendations

## Pages Reviewed

| Page | Route | Status |
|------|-------|--------|
| Battery Dashboard | `/panel/heimdall` (not registered) | ❌ |

## Critical Blocker (Persists from Epic 2)

**The panel is not registered in Home Assistant and cannot be accessed for end-to-end testing.**

- The frontend code exists at `custom_components/heimdall_battery_sentinel/www/panel-heimdall.js`
- Attempted access via `/panel/heimdall` returns 404
- This issue has been noted in Epics 2, 3, and 4 retrospectives but remains unresolved
- **Action required:** Fix panel registration in `__init__.py`

**Root cause analysis:** The panel registration in `__init__.py` uses incorrect parameters:
```python
await hass.components.frontend.async_register_panel(
    "heimdall",
    "frontend",  # Incorrect - should be "javascript"
    "heimdall_battery_sentinel",  # JS module path doesn't exist
    None
)
```

---

## Findings

### 🔴 CRITICAL Issues

#### UX-CRIT-1: Panel Not Registered in Home Assistant

**Page:** N/A - Panel inaccessible
**Spec Reference:** Main Page Layout

**Expected:** Panel should be accessible at `/panel/heimdall` or as a Lovelace panel
**Actual:** Returns 404 Not Found

**Evidence:**
```
$ curl -s -w "\n%{http_code}" http://homeassistant.lan:8123/panel/heimdall
404
```

**Code Analysis (since visual testing unavailable):**
- The JavaScript implementation appears correct for sortable tables
- Last Checked column is rendered with proper date formatting using `toLocaleString()`
- Sort handlers correctly toggle between asc/desc
- Sort state is preserved in API requests

**Recommendation:** Fix panel registration in `__init__.py` - use correct module type and path

---

### 🟡 MEDIUM Issues

#### UX-MED-1: Typography Doesn't Match Token Scale

**Page:** Header
**Spec Reference:** Typography Scale (H6 = 1.25rem/20px)

**Expected:** Page title should use H6 = 20px per spec
**Actual:** h1 uses font-size: 24px

**Code Evidence:**
```javascript
.header h1 {
  margin: 0;
  font-size: 24px;  // Spec says 20px (H6)
  font-weight: 400;
}
```

**Recommendation:** Change font-size to 20px to match H6 token

---

#### UX-MED-2: No Explicit Dark Mode Overrides

**Page:** All
**Spec Reference:** Color Palette - Dark Mode tokens

**Expected:** Explicit dark mode styles using DM tokens from spec
**Actual:** Relies entirely on HA CSS variables without explicit dark overrides

**Code Evidence:**
```javascript
// No @media (prefers-color-scheme: dark) or .dark-theme overrides
// Relies on var(--ha-card-background, #fff) which may not work in all cases
.tab {
  background: var(--ha-card-background, #fff);
}
```

**Recommendation:** Add explicit dark mode overrides using DM tokens (#121212 BG, #1E1E1E surface)

---

### 🟢 LOW Issues

| ID | Issue | Page | Status |
|----|-------|------|--------|
| UX-LOW-1 | Sort icons use Unicode arrows (↑↓) instead of HA icons | Table | Unchanged since Epic 4-1 |
| UX-LOW-2 | Threshold slider shows "(Coming soon)" - not functional | Footer | Unchanged since Epic 4-1 |

---

## Implementation Quality (Code Review)

Since panel is inaccessible, here is a code-based assessment:

### ✅ Correct Implementation

1. **Sort toggle behavior:**
   - Clicking column headers toggles ascending/descending sort ✅
   - Sort indicators show current sort state with active class ✅

2. **Last Checked column:**
   - Added `data-sort="updated_at"` for sorting ✅
   - Date formatting uses `toLocaleString()` for consistent display ✅
   - Proper null handling ("Unknown" fallback) ✅

3. **Sort state persistence:**
   - Sort params sent in API request: `sort_by`, `sort_dir` ✅
   - Resets to page 0 when sort changes ✅

### Partial Implementation

1. **Sortable columns:**
   - Code has: `['friendly_name', 'area', 'battery_level', 'updated_at']`
   - Backend supports: `friendly_name, area, battery_level, entity_id, updated_at`
   - entity_id sorting available in backend but not exposed in frontend UI

---

## Accessibility Audit

| Check | Status | Notes |
|-------|--------|-------|
| Focus indicators | ✅ | .tab:focus and th:focus styles present |
| Tab order | ✅ | tabindex attributes properly set |
| Color contrast | ✅ | Severity colors match spec |
| ARIA labels | ⚠️ | Tabs have roles, table missing row/cell roles |
| Keyboard navigation | ✅ | Arrow keys for tabs, Enter/Space for sorting |
| Screen reader | ⚠️ | Has roles but table structure incomplete |
| Sort keyboard | ✅ | Enter/Space triggers sort on th elements |

---

## Recommendations

### Must Fix (Blocking)

1. **Register Panel in Home Assistant**
   - Fix the `async_register_panel` call in `__init__.py`
   - Use correct module type ("javascript" not "frontend")
   - Ensure JS path is accessible at registered URL

### Should Fix

1. **Fix Typography**
   - Change h1 font-size from 24px to 20px (H6 token)

2. **Add Dark Mode Support**
   - Add explicit dark mode color overrides

3. **Complete Table ARIA Roles**
   - Add role="row" to tr elements
   - Add role="columnheader" to th elements
   - Add role="gridcell" to td elements

### Nice to Have

1. Make threshold slider functional (remove "(Coming soon)")
2. Use HA icons for sort indicators instead of Unicode

---

## Conclusion

**Overall Verdict:** CHANGES_REQUESTED

**Implementation Quality:** The sortable tables feature appears correctly implemented in code:
- ✅ Sort toggle works correctly
- ✅ Last Checked column displays formatted dates
- ✅ Sort state is preserved in API calls

**Critical Blocker:** Panel registration issue persists from prior epics, preventing end-to-end visual verification. This must be resolved before story acceptance.

**Issues from Prior Reviews Still Present:**
1. 🔴 Panel not registered - prevents end-to-end verification
2. 🟡 Typography needs adjustment (24px → 20px)
3. 🟡 No explicit dark mode styles
4. 🟢 Unicode sort icons instead of HA icons
5. 🟢 Threshold slider incomplete

**Next Steps:**
1. Fix panel registration in Home Assistant
2. Fix typography token
3. Add dark mode overrides
4. Complete table ARIA roles
5. Re-run UX review once panel is accessible for visual verification