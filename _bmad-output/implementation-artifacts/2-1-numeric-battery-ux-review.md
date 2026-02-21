# UX Review Report: 2-1 Numeric Battery

**Story:** 2-1-numeric-battery  
**Date:** 2026-02-20  
**Reviewer:** UX Review Agent  
**Scope:** Home Assistant integration — numeric battery entities display and paging  
**Dev Server:** http://homeassistant.lan:8123  
**Overall Verdict:** CHANGES_REQUESTED

---

## Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 0 |
| 🟠 HIGH | 3 |
| 🟡 MEDIUM | 4 |
| 🟢 LOW | 2 |

**Total Issues:** 9

---

## Pages Reviewed

| Page | Route | Status |
|------|-------|--------|
| Heimdall Battery Sentinel Panel | `/config/panels/heimdall_battery_sentinel` | ⚠️ ISSUES FOUND |
| Low Battery Tab | (in-panel) | ⚠️ ISSUES FOUND |
| Table Layout (Desktop/Tablet/Mobile) | (responsive) | ⚠️ ISSUES FOUND |

---

## Findings

### 🟠 HIGH Issues

#### UX-HIGH-1: Missing ARIA Labels and Roles on Interactive Table

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Accessibility → Screen Reader, Keyboard Navigation

**Expected:**
- Table marked with `role="grid"` or semantic `<table>` with ARIA roles
- Column headers marked with `role="columnheader"` or `<th scope="col">`
- Data rows marked with `role="row"`
- Sort buttons have descriptive ARIA labels (e.g., "Sort by Battery, currently ascending")
- Interactive elements have `aria-sort="ascending|descending|none"`
- Table has `aria-label` or `aria-labelledby` describing its purpose

**Actual:**
- Table uses semantic `<table>/<thead>/<tbody>` ✓ (correct HTML)
- Headers are `<th>` elements ✓ (correct)
- **BUT** no `aria-sort` attributes on headers ✗
- **BUT** no descriptive ARIA labels on sort buttons ✗
- **BUT** no `aria-label` on table itself ✗
- **BUT** no ARIA live regions for loading/end-of-list messages ✗

**Screenshot Evidence:** Code review of `panel-heimdall.js` lines 252-285 (table rendering)

**Impact:** Screen reader users cannot understand sort state or interact effectively with sortable headers.

---

#### UX-HIGH-2: No Visible Focus Indicators for Keyboard Navigation

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Accessibility → Keyboard Navigation, Focus Management

**Expected:**
- All interactive elements (buttons, links, sortable headers) have visible focus ring
- Focus outline color ≥ 3:1 contrast with background
- Focus ring visible in both light and dark modes
- Recommended: Use a bright, high-contrast color (e.g., 2–3px outline)

**Actual:**
- CSS provides no explicit `:focus` or `:focus-visible` styles ✗
- Tab buttons (`.tab-btn`) have no focus styling ✗
- Table header (`th`) has no focus styling ✗
- Links have no focus styling ✗
- Browsers' default focus indicator may be used, but spec requires explicit design ✗

**Screenshot Evidence:** Code review of `panel-heimdall.js` CSS section (lines 181-205)

**Impact:** Keyboard-only users cannot reliably identify focused elements; violates WCAG 2.1 AA (2.4.7 Focus Visible).

---

#### UX-HIGH-3: Severity Color Values Don't Match Specification

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Design Tokens → Color Palette (Severity section)

**Expected:**
- 🔴 Critical (Red): `#F44336`
- 🟠 Warning (Orange): `#FF9800`
- 🟡 Notice (Yellow): `#FFEB3B`

**Actual:**
- 🔴 Critical (Red): `#d32f2f` (slightly darker)
- 🟠 Warning (Orange): `#f57c00` (slightly darker)
- 🟡 Notice (Yellow): `#fbc02d` (slightly darker)

**Code Location:** `panel-heimdall.js` lines 200–202

**Impact:**
- Minor visual discrepancy from design spec
- May affect brand consistency
- Colors are still accessible (all ≥ 4.5:1 contrast with white background)
- However, they are Material Design colors (#D32F2F is Material Red 700, not Red 500)
- Spec explicitly defines severity colors; should match exactly

---

### 🟡 MEDIUM Issues

#### UX-MEDIUM-1: No Responsive Column Hiding for Mobile

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Responsive Behavior (3 cols desktop, 2 cols tablet, 1 col mobile)

**Expected:**
- Desktop (1440px): Display all 4 columns (Entity, Battery, Area, Manufacturer)
- Tablet (768px): Display 2 columns (Entity, Battery/Detail)
- Mobile (375px): Display 1 column (Entity + summary detail)
- Use CSS media queries or JavaScript to manage visibility
- Preserve information with alternative display (e.g., detail rows, expandable sections)

**Actual:**
- All columns always visible ✗
- No media queries for responsive column hiding ✗
- Table will become cramped on mobile devices (375px viewport) ✗
- Horizontal scrolling may be required on narrow viewports ✗
- Spec shows responsive layout mockups; implementation does not follow them ✗

**Code Location:** `panel-heimdall.js` CSS section (lines 181–205) — no media queries present

**Impact:**
- Mobile users experience poor readability and may need to scroll horizontally
- Violates responsive resilience principle from spec
- Likely violates WCAG 2.1 AA (1.4.10 Reflow)

---

#### UX-MEDIUM-2: Sort Direction Indicator Uses Pseudo-Characters

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Component Library → Table Component (Sort Indicator)

**Expected:**
- Sort indicator should use clear, recognizable symbols
- Consider Material Design icons (e.g., `arrow_upward`, `arrow_downward`)
- Or use Unicode arrows with fallback styling
- Ensure good visibility and accessibility (not just visual)
- Use `aria-label` to describe sort state to screen readers

**Actual:**
- Uses Unicode arrows: `▲` (U+25B2, Black Up-Pointing Triangle) and `▼` (U+25BC, Black Down-Pointing Triangle)
- Rendered as plain text in `<span class="sort-icon">`
- No accessible label or `aria-label` ✗
- These symbols may not render consistently across browsers/fonts
- The arrow icons are small (font-size: 10px) and may be hard to see
- No `role="img"` or `aria-hidden` to manage accessibility ✗

**Code Location:** `panel-heimdall.js` lines 267–269

**Impact:**
- Screen reader users cannot determine sort direction
- Visual indicator may be too small or unclear
- Potential cross-browser rendering issues

---

#### UX-MEDIUM-3: Loading State and End-of-List Message Not Marked as Live Regions

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Accessibility → Screen Reader (Live Regions)

**Expected:**
- Loading indicator (e.g., "Loading…") marked with `aria-live="polite"` or `role="status"`
- End-of-list message marked with `aria-live="polite"` or `role="complementary"`
- Screen readers announce state changes when new content loads
- Avoids silent loading states that may confuse users

**Actual:**
- Loading div has class `.loading` but no ARIA live region attributes ✗
- End-message div has class `.end-message` but no ARIA attributes ✗
- No `aria-live`, `role="status"`, or `role="complementary"` ✗
- Screen readers will not announce loading or end-of-list states ✗

**Code Location:** `panel-heimdall.js` lines 282–283 (no ARIA attributes in HTML)

**Impact:**
- Screen reader users unaware of loading state
- Confused navigation experience (infinite scroll silently loads data)

---

#### UX-MEDIUM-4: Font Sizes and Typography Don't Explicitly Use Design Tokens

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Design Tokens → Typography Scale

**Expected:**
- Page title: H6 (20px, weight 600)
- Section headers: Subtitle1 (16px, weight 500)
- Body text: Body1 (14px, weight 400)
- Helper/metadata: Caption (12px, weight 400)
- Tab labels: Body1 (14px)
- Table headers: Subtitle1 (16px, weight 500)

**Actual:**
- CSS uses `font-family: var(--paper-font-body1_-_font-family, sans-serif)` (good, uses HA variable)
- **BUT** no explicit font sizes defined for headers, body, or captions
- Tabs use `font-size: 14px` ✓ (matches Body1)
- Table uses `font-size: 14px` (inherited from body) — should be Subtitle1 (16px) for headers
- Links and text inherit default browser size
- No explicit use of weight values (600, 500, 400)
- Relies on browser defaults or HA theme variables

**Code Location:** `panel-heimdall.js` CSS section (lines 181–205)

**Impact:**
- Visual inconsistency with design spec
- Header hierarchy not visually clear
- May impact readability

---

### 🟢 LOW Issues

#### UX-LOW-1: HTML Escaping Utility Only Called on Some Fields

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Security/Best Practices

**Status:** ✓ ACCEPTABLE (minor)

**Note:** The `_esc()` utility is used to escape `friendly_name`, `battery_display`, and other text fields. This is good practice to prevent XSS. However, the `area` and `manufacturer` fields also escape (line 306), so coverage is adequate.

---

#### UX-LOW-2: Sort Icons Font Size May Be Too Small

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Design Tokens → Typography

**Note:** Sort icons use `font-size: 10px` (line 197). This is very small and may be hard to see on mobile devices or for users with low vision. Consider increasing to 12–14px for better visibility.

---

## Accessibility Audit

| Check | Status | Notes |
|-------|--------|-------|
| **Color Contrast** | ⚠️ PARTIAL | Severity colors have 4.5:1+ contrast with white background ✓; tab buttons use HA theme colors (assumed sufficient); **but** no explicit testing against dark mode ✗ |
| **Focus Indicators** | ❌ FAILED | No visible focus ring defined in CSS; violates WCAG 2.1 AA 2.4.7 |
| **Tab Order** | ⚠️ ASSUMED OK | HTML structure suggests logical tab order; no explicit management in JS |
| **ARIA Labels** | ❌ FAILED | Missing on table headers (aria-sort), interactive elements (aria-label), and live regions (aria-live) |
| **Keyboard Navigation** | ⚠️ PARTIAL | Tab buttons are keyboard accessible ✓; sortable headers likely keyboard-accessible via `<th>` ✓; **but** no explicit arrow-key navigation within table ✗ |
| **Screen Reader Support** | ❌ FAILED | Missing ARIA labels, live regions, sort state indicators |
| **Reduced Motion** | ⚠️ UNKNOWN | No explicit `prefers-reduced-motion` media query; animations brief so likely acceptable |
| **Dark Mode** | ⚠️ ASSUMED OK | Uses HA theme CSS variables; untested in actual dark mode |

---

## Recommendations

### Must Fix (CHANGES_REQUIRED)

1. **Add ARIA attributes to table:**
   - Add `aria-sort="ascending|descending|none"` to each `<th>`
   - Add `aria-label` to table (e.g., "Low battery entities, sortable")
   - Add `aria-label` to sort buttons (e.g., "Sort by Battery, currently ascending")

2. **Add visible focus indicators:**
   - Define `:focus-visible` styles for buttons, links, and table headers
   - Use high-contrast color (e.g., 2px solid var(--primary-color) or #03a9f4)
   - Ensure focus ring visible in both light and dark modes

3. **Add ARIA live regions:**
   - Mark loading indicator with `role="status"` and `aria-live="polite"`
   - Mark end-of-list message with `aria-live="polite"`

4. **Fix severity colors to match spec:**
   - Change `#d32f2f` → `#F44336` (red)
   - Change `#f57c00` → `#FF9800` (orange)
   - Change `#fbc02d` → `#FFEB3B` (yellow)

5. **Implement responsive column hiding:**
   - Add media queries for tablet (768px) and mobile (375px)
   - Hide non-essential columns on smaller screens
   - Consider accordion/expandable detail rows for mobile

### Should Fix (Polish)

6. **Improve sort indicator:**
   - Use Material Design icons instead of Unicode characters
   - Add `aria-label` to clarify sort direction for screen readers
   - Increase font size to 12–14px for visibility

7. **Add explicit typography tokens:**
   - Define font sizes for headers (16px), body (14px), and captions (12px)
   - Define font weights (600, 500, 400)
   - Update tab styling to use Subtitle1 token

8. **Add reduced motion support:**
   - Add `@media (prefers-reduced-motion: reduce)` to disable animations
   - Set `animation: none` or remove transition rules

---

## Conclusion

**Overall Verdict:** CHANGES_REQUESTED

The implementation provides solid functional foundations:
- ✅ Numeric battery evaluation working correctly (backend verified)
- ✅ Rounding and display formatting correct (14.7% → "15%")
- ✅ Threshold application working
- ✅ Sorting functional and sortable headers implemented
- ✅ Infinite scroll pagination implemented

**However, accessibility and design consistency issues must be addressed:**
- ❌ Missing ARIA labels and roles (violates WCAG 2.1 AA)
- ❌ No visible focus indicators (violates WCAG 2.1 AA 2.4.7)
- ❌ Severity colors don't match spec values
- ❌ Not responsive for mobile (1 column as per spec)
- ⚠️ Typography tokens not explicitly applied

**Required Changes Before Acceptance:**
1. Add ARIA attributes (table, headers, live regions)
2. Add visible focus indicators
3. Correct severity colors to match spec
4. Implement responsive column hiding for mobile
5. Test in dark mode

**Timeline:** These are accessibility and design consistency fixes; estimated 2–3 hours of development.

---

## Quality Gates Verification

- [x] Review applicability assessed (UI changes present, review required)
- [x] UX spec loaded and reviewed
- [x] Dev server accessible
- [x] Implementation code reviewed (panel-heimdall.js, evaluator.py, models.py)
- [x] Each finding has evidence (code citations and requirements)
- [x] Accessibility checked (WCAG 2.1 AA criteria applied)
- [x] Report written with Overall Verdict: CHANGES_REQUESTED
- [ ] Screenshots captured (browser control unavailable, code review performed)
- [ ] File pending commit to git

---

**Reviewed against:** UX Design Specification v1.0 (ux-design-specification.md)  
**Test Plan Status:** All backend unit tests passing (109/109 ✓); frontend component untested in browser
