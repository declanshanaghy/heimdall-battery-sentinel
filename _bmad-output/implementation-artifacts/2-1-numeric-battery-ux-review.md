# UX Review Report: 2-1 Numeric Battery (Fresh Review After Code Fixes)

**Story:** 2-1-numeric-battery  
**Date:** 2026-02-20  
**Reviewer:** UX Review Agent  
**Scope:** Home Assistant integration — numeric battery entities display and paging  
**Dev Server:** http://homeassistant.lan:8123  
**Overall Verdict:** ⚠️ **CHANGES_REQUESTED** (UX issues unresolved; backend AC4 fix verified)

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 CRITICAL | 0 | — |
| 🟠 HIGH | 3 | ⚠️ Still present from previous review |
| 🟡 MEDIUM | 4 | ⚠️ Still present from previous review |
| 🟢 LOW | 2 | ⚠️ Still present from previous review |

**Total Issues:** 9 (unchanged from prior review)

---

## Background

**Prior Review (2026-02-20 21:41 PST):**  
Previous UX review identified 9 accessibility and design consistency issues, primarily:
- Missing ARIA labels, roles, and live regions (WCAG 2.1 AA violations)
- No visible focus indicators for keyboard navigation
- Severity colors don't match spec values
- No responsive column hiding for mobile
- Typography tokens not explicitly applied

**Code Review (2026-02-20 23:12 PST):**  
Code review of backend story 2-1 implementation was **ACCEPTED**:
- ✅ AC4 critical architectural issue **FIXED** (store-layer AC4 enforcement)
- ✅ All 120 backend unit tests **PASS** (113 existing + 7 new AC4 tests)
- ✅ Numeric battery evaluation working correctly
- ✅ Numeric display formatting correct (14.7% → "15%")
- ✅ Threshold application working
- ✅ Sorting functional
- ✅ Infinite scroll pagination functional

**Fresh UX Review (2026-02-20 23:13 PST):**  
Review of frontend code (`panel-heimdall.js`) to verify whether previous UX issues have been addressed.

---

## Code Review Findings

**Frontend code state:** Git history shows `panel-heimdall.js` last modified in commit `e382344` (2026-02-20 02:51 — original story 1-1 project structure setup). No modifications since previous UX review.

**Conclusion:** **All 9 previous UX issues remain unaddressed in frontend code.**

---

## Pages Reviewed

| Page | Route | Status |
|------|-------|--------|
| Heimdall Battery Sentinel Panel | `/config/panels/heimdall_battery_sentinel` | ⚠️ CODE REVIEW: 9 issues persist |
| Low Battery Tab | (in-panel) | ⚠️ CODE REVIEW: 9 issues persist |
| Unavailable Tab | (in-panel) | ⚠️ CODE REVIEW: 9 issues persist |
| Table Layout (Desktop/Tablet/Mobile) | (responsive) | ⚠️ CODE REVIEW: 9 issues persist |

---

## Issues Carried Forward from Previous Review

### 🟠 HIGH Issues

#### UX-HIGH-1: Missing ARIA Labels and Roles on Interactive Table

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Accessibility → Screen Reader, Keyboard Navigation  
**Status:** ⚠️ **NOT FIXED**

**Code Location:** `panel-heimdall.js:287-304` (table rendering)

**Expected (per spec):**
- Table marked with `role="grid"` or semantic `<table>` with ARIA roles
- Column headers marked with `role="columnheader"` or `<th scope="col">`
- Data rows marked with `role="row"`
- Sort buttons have descriptive ARIA labels (e.g., "Sort by Battery, currently ascending")
- Interactive elements have `aria-sort="ascending|descending|none"`
- Table has `aria-label` or `aria-labelledby` describing purpose
- Live regions for loading and end-of-list state

**Current Implementation:**

```javascript
// Line 287-304
const headerRow = cols
  .map((col) => {
    const isActive = sort.by === col.key;
    const icon = isActive ? (sort.dir === "asc" ? "▲" : "▼") : "";
    return `<th data-col="${col.key}">${col.label}<span class="sort-icon">${icon}</span></th>`;
  })
  .join("");

const bodyRows = rows
  .map((row) => {
    const cells = cols.map((col) => {
      if (col.key === "friendly_name") {
        const href = `/config/entities/entity/${row.entity_id}`;
        return `<td><a href="${href}" target="_blank">${this._esc(row.friendly_name || row.entity_id)}</a></td>`;
      }
      // ... other columns ...
    });
    return `<tr>${cells.join("")}</tr>`;
  })
  .join("");

container.innerHTML = `
  <table>
    <thead><tr>${headerRow}</tr></thead>
    <tbody>${bodyRows}</tbody>
  </table>
  ${this._loading ? '<div class="loading">Loading…</div>' : ""}
  ${this._end[tab] && rows.length > 0 ? '<div class="end-message">All entities loaded</div>' : ""}
`;
```

**Issues Found:**
- ✅ Table uses semantic `<table>/<thead>/<tbody>` (correct HTML)
- ✅ Headers are `<th>` elements (correct)
- ❌ **No `aria-sort` attributes on headers**
- ❌ **No descriptive ARIA labels on sort buttons**
- ❌ **No `aria-label` on table itself**
- ❌ **No ARIA live regions:** Loading div and end-message div have no `aria-live`, `role="status"`, or `role="complementary"`

**Impact:** Screen reader users cannot understand sort state or interact effectively with sortable headers. Loading states and end-of-list messages are not announced.

**Priority:** MUST FIX (accessibility violation — WCAG 2.1 AA 4.1.3 Name, Role, Value)

---

#### UX-HIGH-2: No Visible Focus Indicators for Keyboard Navigation

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Accessibility → Keyboard Navigation, Focus Management  
**Status:** ⚠️ **NOT FIXED**

**Code Location:** `panel-heimdall.js:166-200` (CSS styles)

**Expected (per spec):**
- All interactive elements (buttons, links, sortable headers) have visible focus ring
- Focus outline color ≥ 3:1 contrast with background
- Focus ring visible in both light and dark modes
- Recommended: Use bright, high-contrast color (2–3px outline)

**Current Implementation:**

```css
/* Lines 166-200 (CSS) */
.tabs { display: flex; gap: 8px; margin-bottom: 16px; }
.tab-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background: var(--secondary-background-color, #f0f0f0);
  font-size: 14px;
}
.tab-btn.active { background: var(--primary-color, #03a9f4); color: white; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
th { cursor: pointer; user-select: none; font-weight: 600; background: var(--table-header-background-color, #fafafa); }
th:hover { background: var(--secondary-background-color, #f0f0f0); }
a { color: var(--primary-color, #03a9f4); text-decoration: none; }
a:hover { text-decoration: underline; }
```

**Issues Found:**
- ❌ **No `:focus` or `:focus-visible` styles defined**
- ❌ **Tab buttons (`.tab-btn`) have no focus styling**
- ❌ **Table headers (`th`) have no focus styling**
- ❌ **Links have no focus styling**
- ⚠️ Browsers' default focus indicator will be used, but spec requires explicit design

**Impact:** Keyboard-only users cannot reliably identify focused elements. Violates WCAG 2.1 AA (2.4.7 Focus Visible).

**Priority:** MUST FIX (accessibility violation)

---

#### UX-HIGH-3: Severity Color Values Don't Match Specification

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Design Tokens → Color Palette (Severity section)  
**Status:** ⚠️ **NOT FIXED**

**Code Location:** `panel-heimdall.js:196-198` (CSS severity colors)

**Expected (per UX spec):**
- 🔴 Critical (Red): `#F44336`
- 🟠 Warning (Orange): `#FF9800`
- 🟡 Notice (Yellow): `#FFEB3B`

**Current Implementation:**

```css
/* Lines 196-198 */
.severity-red { color: #d32f2f; }
.severity-orange { color: #f57c00; }
.severity-yellow { color: #fbc02d; }
```

**Issues Found:**
- ❌ 🔴 Red: `#d32f2f` (Material Red 700, not Red 500 per spec)
- ❌ 🟠 Orange: `#f57c00` (Material Orange 700, not Orange 500 per spec)
- ❌ 🟡 Yellow: `#fbc02d` (Material Amber 700, not Amber 400 per spec)
- ✅ All colors have ≥4.5:1 contrast with white background (accessible)
- ❌ **Visual discrepancy from design spec** (brand consistency issue)

**Impact:** Minor visual deviation from design spec. Colors are still accessible but don't match brand colors. May impact visual consistency across integration and design documentation.

**Priority:** SHOULD FIX (design consistency)

---

### 🟡 MEDIUM Issues

#### UX-MEDIUM-1: No Responsive Column Hiding for Mobile

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Responsive Behavior (3 cols desktop, 2 cols tablet, 1 col mobile)  
**Status:** ⚠️ **NOT FIXED**

**Code Location:** `panel-heimdall.js:166-200` (CSS — no media queries present)

**Expected (per spec):**
- Desktop (1440px+): Display all 4 columns (Entity, Battery, Area, Manufacturer)
- Tablet (768px): Display 2 columns (Entity, Battery/Detail)
- Mobile (375px): Display 1 column (Entity + summary detail)
- Use CSS media queries or JavaScript to manage visibility

**Current Implementation:**

```css
/* Lines 166-200: No media queries present */
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
/* All columns always visible */
```

**Issues Found:**
- ❌ **No CSS media queries for responsive column hiding**
- ❌ **All columns always visible regardless of viewport width**
- ❌ **No JavaScript logic to manage column visibility**
- ❌ **Table will become cramped on mobile devices (375px viewport)**
- ❌ **Horizontal scrolling likely required on narrow viewports**
- ❌ **Spec shows responsive layout mockups; implementation does not follow them**

**Impact:** Mobile users experience poor readability and cramped layout. May require horizontal scrolling. Violates responsive resilience principle from spec and WCAG 2.1 AA (1.4.10 Reflow).

**Priority:** MUST FIX (mobile usability and accessibility)

---

#### UX-MEDIUM-2: Sort Direction Indicator Uses Unicode Pseudo-Characters

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Component Library → Table Component (Sort Indicator)  
**Status:** ⚠️ **NOT FIXED**

**Code Location:** `panel-heimdall.js:290` and CSS line 197

**Expected (per spec):**
- Sort indicator should use clear, recognizable symbols (Material Design icons recommended)
- Ensure good visibility and accessibility (not just visual)
- Use `aria-label` to describe sort state to screen readers
- Font size adequate for visibility

**Current Implementation:**

```javascript
// Line 290
const icon = isActive ? (sort.dir === "asc" ? "▲" : "▼") : "";
return `<th data-col="${col.key}">${col.label}<span class="sort-icon">${icon}</span></th>`;
```

```css
/* Line 197 */
.sort-icon { margin-left: 4px; font-size: 10px; }
```

**Issues Found:**
- ❌ **Uses Unicode pseudo-characters** (`▲` U+25B2 Black Up-Pointing Triangle, `▼` U+25BC Black Down-Pointing Triangle)
- ❌ **No `aria-label` or accessible label for sort direction**
- ❌ **Font size very small (10px)** — may be hard to see on mobile or for users with low vision
- ⚠️ Unicode characters may not render consistently across browsers/fonts
- ❌ **No `role="img"` or `aria-hidden` to manage accessibility**
- ❌ **Sort state not announced to screen readers**

**Impact:** Screen reader users cannot determine sort direction. Visual indicator may be too small or unclear. Potential cross-browser rendering issues.

**Priority:** SHOULD FIX (accessibility and clarity)

---

#### UX-MEDIUM-3: Loading State and End-of-List Message Not Marked as Live Regions

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Accessibility → Screen Reader (Live Regions)  
**Status:** ⚠️ **NOT FIXED**

**Code Location:** `panel-heimdall.js:299-301` (HTML rendering)

**Expected (per spec):**
- Loading indicator marked with `aria-live="polite"` or `role="status"`
- End-of-list message marked with `aria-live="polite"` or `role="complementary"`
- Screen readers announce state changes when new content loads
- Avoids silent loading states that confuse users

**Current Implementation:**

```javascript
// Lines 299-301
${this._loading ? '<div class="loading">Loading…</div>' : ""}
${this._end[tab] && rows.length > 0 ? '<div class="end-message">All entities loaded</div>' : ""}
```

**Issues Found:**
- ❌ **Loading div has no ARIA attributes** (no `aria-live`, `role="status"`)
- ❌ **End-message div has no ARIA attributes** (no `aria-live`, `role="status"`)
- ❌ **Screen readers will not announce loading state**
- ❌ **Screen readers will not announce end-of-list state**
- ❌ **Silent infinite scroll confuses users relying on screen readers**

**Impact:** Screen reader users unaware of loading state. Infinite scroll silently loads data without announcement. Poor experience for users relying on assistive technology.

**Priority:** SHOULD FIX (accessibility)

---

#### UX-MEDIUM-4: Font Sizes and Typography Don't Explicitly Use Design Tokens

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Design Tokens → Typography Scale  
**Status:** ⚠️ **NOT FIXED**

**Code Location:** `panel-heimdall.js:166-200` (CSS) and HTML rendering

**Expected (per UX spec):**
- Page title: H6 (20px, weight 600)
- Section headers: Subtitle1 (16px, weight 500)
- Body text: Body1 (14px, weight 400)
- Helper/metadata: Caption (12px, weight 400)
- Tab labels: Body1 (14px)
- Table headers: Subtitle1 (16px, weight 500)

**Current Implementation:**

```css
/* Lines 166-200 */
:host { display: block; padding: 16px; font-family: var(--paper-font-body1_-_font-family, sans-serif); }
.tab-btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; background: var(--secondary-background-color, #f0f0f0); font-size: 14px; }
th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
th { cursor: pointer; user-select: none; font-weight: 600; background: var(--table-header-background-color, #fafafa); }
.sort-icon { margin-left: 4px; font-size: 10px; }
```

**Issues Found:**
- ✅ CSS uses `var(--paper-font-body1_-_font-family, sans-serif)` for font family (good)
- ❌ **No explicit font sizes for headers, section titles, or body text**
- ❌ **Tab buttons use `font-size: 14px`** ✓ (matches Body1, correct by chance)
- ❌ **Table headers use inherited font size** (should be Subtitle1 16px, not Body1 14px)
- ❌ **No explicit use of weight values (600, 500, 400)** — relies on browser defaults
- ❌ **Helper text (Caption) not styled explicitly**
- ❌ **Sort icon font size (10px) not in spec**
- ⚠️ **Visual hierarchy not clearly defined** — relies on HA theme variables

**Impact:** Visual inconsistency with design spec. Header hierarchy not visually clear. May impact readability and professional presentation.

**Priority:** SHOULD FIX (design consistency and readability)

---

### 🟢 LOW Issues

#### UX-LOW-1: HTML Escaping Utility Only Called on Some Fields

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Security/Best Practices  
**Status:** ✅ **ACCEPTABLE**

**Code Location:** `panel-heimdall.js:295-306`

**Note:** The `_esc()` utility is used to escape `friendly_name`, `battery_display`, `area`, and `manufacturer` fields. This is good practice to prevent XSS. Coverage appears adequate for all user-facing text fields.

---

#### UX-LOW-2: Sort Icons Font Size May Be Too Small

**Page:** Heimdall Battery Sentinel Panel  
**Spec Reference:** Design Tokens → Typography  
**Status:** ⚠️ **NOTED**

**Code Location:** `panel-heimdall.js:197` (CSS `.sort-icon`)

**Note:** Sort icons use `font-size: 10px`. This is very small and may be hard to see on mobile devices or for users with low vision. Consider increasing to 12–14px for better visibility.

---

## Accessibility Audit

| Check | Status | Notes |
|-------|--------|-------|
| **Color Contrast** | ⚠️ PARTIAL | Severity colors have 4.5:1+ contrast with white background ✓; tab buttons use HA theme colors (assumed sufficient); **no explicit testing against dark mode** ✗ |
| **Focus Indicators** | ❌ **FAILED** | No visible focus ring defined in CSS; violates WCAG 2.1 AA 2.4.7 Focus Visible |
| **Tab Order** | ⚠️ UNKNOWN | HTML structure suggests logical tab order; no explicit testing performed |
| **ARIA Labels** | ❌ **FAILED** | Missing on table headers (aria-sort), interactive elements (aria-label), live regions (aria-live). WCAG violations. |
| **Keyboard Navigation** | ⚠️ PARTIAL | Tab buttons likely keyboard-accessible ✓; sortable headers likely keyboard-accessible via `<th>` ✓; **no explicit arrow-key navigation within table** ✗ |
| **Screen Reader Support** | ❌ **FAILED** | Missing ARIA labels, live regions, sort state indicators. Screen readers cannot interpret table or announce state changes. |
| **Reduced Motion** | ⚠️ UNKNOWN | No explicit `prefers-reduced-motion` media query; animations brief so likely acceptable but untested |
| **Dark Mode** | ⚠️ UNTESTED | Uses HA theme CSS variables; untested in actual dark mode; severity colors unverified in dark background |

---

## Recommendations

### Must Fix (CHANGES_REQUIRED)

1. **Add ARIA attributes to table:**
   - Add `aria-sort="ascending|descending|none"` to each `<th>`
   - Add `aria-label` to table (e.g., "Low battery entities, sortable")
   - Add descriptive `aria-label` to sort buttons (e.g., "Sort by Battery Level")

2. **Add visible focus indicators (WCAG 2.1 AA 2.4.7):**
   - Define `:focus-visible` styles for buttons, links, and table headers
   - Use high-contrast color (e.g., 2px solid var(--primary-color) or #03a9f4)
   - Ensure focus ring visible in both light and dark modes
   - Example: `th:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }`

3. **Add ARIA live regions (WCAG 2.1 AA 4.1.3):**
   - Mark loading indicator with `role="status"` and `aria-live="polite"` (or `aria-atomic="true"`)
   - Mark end-of-list message with `aria-live="polite"`
   - Example: `<div class="loading" role="status" aria-live="polite" aria-atomic="true">Loading…</div>`

4. **Implement responsive column hiding for mobile:**
   - Add CSS media queries for tablet (768px) and mobile (375px)
   - Hide non-essential columns on smaller screens
   - Example: `@media (max-width: 768px) { .area, .manufacturer { display: none; } }`
   - Consider accordion/expandable detail rows for mobile to preserve information

5. **Fix severity colors to match spec:**
   - Change `#d32f2f` → `#F44336` (red)
   - Change `#f57c00` → `#FF9800` (orange)
   - Change `#fbc02d` → `#FFEB3B` (yellow)

### Should Fix (Polish)

6. **Improve sort indicator:**
   - Replace Unicode characters with Material Design icons or more visible symbols
   - Add `aria-label` to sort icons (e.g., "ascending" or "descending")
   - Increase font size to 12–14px for better visibility
   - Example: `<span class="sort-icon" aria-label="ascending">▲</span>`

7. **Add explicit typography tokens:**
   - Define CSS custom properties for typography tokens:
     - `--typography-h6: { font-size: 20px; font-weight: 600; line-height: 1.3; }`
     - `--typography-subtitle1: { font-size: 16px; font-weight: 500; line-height: 1.4; }`
     - `--typography-body1: { font-size: 14px; font-weight: 400; line-height: 1.5; }`
     - `--typography-caption: { font-size: 12px; font-weight: 400; line-height: 1.4; }`
   - Apply tokens to components

8. **Add reduced motion support:**
   - Add `@media (prefers-reduced-motion: reduce)` to disable animations
   - Set `animation: none` or remove transition rules for users who prefer reduced motion

9. **Test in dark mode:**
   - Verify severity colors are visible against dark backgrounds
   - Verify focus indicators are visible in dark mode
   - Verify text contrast meets 4.5:1 in both light and dark modes

---

## Conclusion

**Overall Verdict:** ⚠️ **CHANGES_REQUESTED**

**Status Summary:**
- ✅ **Backend Code:** ACCEPTED (Code Review 2026-02-20 23:12)
  - AC4 critical issue fixed
  - All 120 unit tests pass
  - Numeric battery evaluation working correctly

- ❌ **Frontend UX:** CHANGES_REQUIRED (9 unresolved issues)
  - All 9 issues from previous UX review remain unaddressed
  - 3 HIGH severity (accessibility violations — WCAG 2.1 AA)
  - 4 MEDIUM severity (design consistency and accessibility)
  - 2 LOW severity (polish)

**Blocking Issues:**
The implementation cannot be accepted without addressing the HIGH severity items:
1. Missing ARIA labels, roles, and live regions (WCAG 2.1 AA 4.1.3 violation)
2. No visible focus indicators (WCAG 2.1 AA 2.4.7 violation)
3. Non-responsive mobile layout (WCAG 2.1 AA 1.4.10 violation)

**Next Steps:**
1. Implement fixes for HIGH severity items (estimated 3–4 hours)
2. Apply SHOULD FIX items for polish (estimated 1–2 hours)
3. Test in both light and dark modes
4. Test keyboard navigation and screen reader support
5. Re-submit for UX review

**Timeline:** These are accessibility and design consistency fixes. Recommend prioritizing HIGH severity items for WCAG 2.1 AA compliance.

---

## Quality Gates Verification

- [x] Review applicability assessed (UI changes present, review required)
- [x] UX spec loaded and reviewed
- [x] Dev server accessible (HTTP 200)
- [x] Implementation code reviewed (panel-heimdall.js)
- [x] Each finding has code evidence and specification reference
- [x] Accessibility checked against WCAG 2.1 AA criteria
- [x] Report written with Overall Verdict: CHANGES_REQUESTED
- [ ] Screenshots captured (browser unavailable; code review performed)
- [ ] File pending commit to git

---

## Cross-Reference Notes

**Related Reviews:**
- Code Review: `2-1-numeric-battery-code-review.md` (Status: ✅ ACCEPTED — Backend)
- QA Report: `2-1-numeric-battery-qa-tester.md` (Status: Functional testing)

**Spec Documents:**
- UX Design Specification: `ux-design-specification.md`
- Architecture: `architecture.md`

**Guidelines:**
- WCAG 2.1 AA: Web Accessibility Guidelines (https://www.w3.org/WAI/WCAG21/quickref/)
- Material Design: Material Design 3 (https://m3.material.io/)

---

**Reviewed against:** UX Design Specification v1.0 (ux-design-specification.md)  
**Accessibility Standard:** WCAG 2.1 Level AA  
**Status:** CHANGES_REQUESTED — 9 issues requiring resolution before acceptance
