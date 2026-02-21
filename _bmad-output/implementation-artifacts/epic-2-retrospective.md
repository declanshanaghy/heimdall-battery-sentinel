# Epic 2 Retrospective: Battery Monitoring

**Epic:** Battery Monitoring | **Stories:** 3 | **Date:** 2026-02-21

## What Went Well ✅

- **Story 2-2 Clean Path**: Built on 2-1's foundation with zero review iterations—single pass through all reviewers. Demonstrates effective knowledge transfer and architectural clarity.
- **Proactive Accessibility Implementation**: Story 2-1 flagged 9 accessibility issues early; team responded with comprehensive WCAG 2.1 AA fixes (ARIA attributes, focus indicators, responsive design). All 27 automated checks passed.
- **Comprehensive Test Coverage**: 148 total tests across epic with detailed AC validation (unit + integration). AC4 incremental path caught and fixed during code review.

## Technical Patterns Established

- **Battery Evaluation Separation**: Clear numeric (%) vs. textual ('low') evaluation paths in evaluate_battery_state(). Each has explicit rules (unit check, state normalization) with graceful logging.
- **Severity Ratio Calculation**: Ratio-based thresholds (critical: 0–33%, warning: 34–66%, notice: 67–100%) provide consistent severity mapping across thresholds. Testable with boundary validation.
- **Store-Layer Constraint Enforcement**: AC4 (one battery per device) enforced in store.upsert_low_battery()—not just batch path. Prevents inconsistency from incremental state_changed events.
- **Frontend Accessibility Patterns**: ARIA attributes on interactive elements (aria-sort, aria-label, aria-live), :focus-visible for keyboard navigation, CSS media queries for responsive behavior (768px/375px breakpoints).

## Critical Risks

- **AC4 Architectural Gap (RESOLVED)**: Initial implementation only filtered AC4 in batch_evaluate(), not incremental events. Code review caught this; store layer enforcement added with 7 new test cases. **Impact:** Could have shipped production bug allowing duplicate batteries per device.
- **UX Accessibility as Follow-up**: 9 issues identified after story 2-1 code review complete. Added iteration cost (UX review 2 cycles). **Lesson:** Accessibility requires frontend-first review, not code-first.
- **Story 2-3 Acceptance Ambiguity**: Story acceptance report iterated once (CHANGES_REQUESTED → ACCEPTED) with no documented root cause. Code review and QA both passed first try. **Unclear what acceptance validates beyond other reviews.**

## Recommendations to Carry Forward

1. **AC4-Type Invariants**: For epics 3+ with incremental events, flag acceptance criteria that depend on "state consistency" (one-per-X patterns). Require both batch AND event handler test coverage from day 1.
2. **UX Accessibility Checklist**: Add WCAG 2.1 AA checks to story definition phase (before dev). Prevents 9-issue discovery post-code-review. Consider automated linting (lighthouse-ci, pa11y) in test suite.
3. **Story Acceptance Clarity**: Document what story acceptance validates that code/QA/UX reviews don't. Current ambiguity risks rework if acceptance criteria are unclear.
