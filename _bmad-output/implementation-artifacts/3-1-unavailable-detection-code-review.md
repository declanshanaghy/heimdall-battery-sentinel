# Code Review Report

**Story:** 3-1-unavailable-detection
**Reviewer:** anthropic/claude-haiku-4-5
**Date:** 2026-02-21
**Overall Verdict:** CHANGES_REQUESTED

## Prior Epic Recommendations

| Recommendation | Source Epic | Status |
|---------------|-------------|--------|
| AC4-Type Invariants: For incremental events, require both batch AND event handler test coverage from day 1 | Epic 2 | ❌ **VIOLATED** — Test for `test_unavailable_version_increments` only checks `bulk_set_unavailable()`, not incremental upsert/remove operations. Missing verification that versions increment on state_changed events. |
| Graceful Error Boundaries: Event handlers wrapped in try/except with structured logging | Epic 1 | ✅ Followed — `_handle_state_changed()` has try/except wrapper with structured error logging |
| Store-Layer Constraint Enforcement: AC4-type invariants enforced in store.upsert_*(), not just batch path | Epic 2 | ⚠️ **PARTIAL** — Low battery enforces AC4 per-device filtering in `upsert_low_battery()`, but no tests verify versioning on incremental operations. |

## Checklist Verification

- [x] Story file loaded and parsed
- [x] Story status verified as reviewable (was: review)
- [x] Acceptance Criteria cross-checked against implementation
- [x] File List reviewed and validated for completeness
- [x] Code quality review performed on changed files
- [x] Security review performed
- [x] Tests examined for real assertions vs. placeholders

## Acceptance Criteria Validation

| AC | Status | Evidence |
|----|--------|----------|
| AC1: System detects unavailable state changes | **PASS** | `evaluate_unavailable_state()` checks `state.state == "unavailable"` and returns UnavailableRow; called from `_handle_state_changed()` on every state change. Tests: `test_unavailable_included`, `test_non_unavailable_excluded`, `test_evaluate_unavailable`. |
| AC2: Entities added to dataset within 5 seconds | **PASS** | Synchronous event handler with direct `store.upsert_unavailable()` call; no async delays. Docstring confirms <100ms latency. |
| AC3: Entities removed when state changes from unavailable | **PASS** | `evaluate_unavailable()` returns None when state != "unavailable"; `store.remove_unavailable()` called on None result. Tests: `test_state_change_removes_unavailable_entry`. |
| AC4: Dataset versioning increments when Unavailable dataset changes | **FAIL** | ❌ Critical issue detected — versions increment ONLY on `bulk_set_unavailable()`, NOT on incremental `upsert_unavailable()` or `remove_unavailable()`. State_changed events trigger upsert/remove but version remains static. |

## Findings

### 🔴 CRITICAL Issues

| ID | Finding | File:Line | Resolution |
|----|---------|-----------|------------|
| CRIT-1 | AC4 Violation: `upsert_unavailable()` modifies dataset but does NOT increment `_unavailable_version`. Cache invalidation will fail for incremental state changes. | store.py:234-250 | Increment `self._unavailable_version += 1` in both `upsert_unavailable()` and `remove_unavailable()` methods, OR move version increment to a common update method. Add tests: `test_unavailable_version_increments_on_upsert()` and `test_unavailable_version_increments_on_remove()`. |
| CRIT-2 | AC4 Violation: `remove_unavailable()` modifies dataset but does NOT increment `_unavailable_version`. Frontend cache will not invalidate. | store.py:252-269 | Same fix as CRIT-1. Version must increment on every dataset mutation, not just bulk operations. |
| CRIT-3 | Test Coverage Gap: `test_unavailable_version_increments()` only tests bulk_set, not incremental operations (upsert/remove). Missing verification that versions increment during state_changed event handling. | test_event_subscription.py:~line 293-304 | Add comprehensive tests: (1) Test version increments when entity becomes unavailable via state_changed event, (2) Test version increments when entity becomes available via state_changed event. Both must verify version > previous_version. |

### 🟠 HIGH Issues

| ID | Finding | File:Line | Resolution |
|----|---------|-----------|------------|
| HIGH-1 | SAME ISSUE IN LOW BATTERY: `upsert_low_battery()` and `remove_low_battery()` do NOT increment `_low_battery_version` on incremental changes, violating versioning design for cache invalidation. This affects both datasets. | store.py:106-184 and store.py:188-201 | Increment `self._low_battery_version += 1` in both methods. This is a design-level issue affecting the entire event-driven cache architecture (ADR-002). |
| HIGH-2 | Incremental Versioning Design Flaw: Only `bulk_set_*()` increments versions, but `_handle_state_changed()` calls `upsert_*()` and `remove_*()` for real-time updates. This breaks cache invalidation for 99% of mutations after initial load. Frontend will serve stale data. | store.py + __init__.py | Move version increment into `upsert_*()` and `remove_*()` methods, OR introduce a common `_mutate_dataset()` wrapper that increments version. This is a critical architectural issue that contradicts the ADR-002 event-driven design principle. |

### 🟡 MEDIUM Issues

| ID | Finding | File:Line | Resolution |
|----|---------|-----------|------------|
| MED-1 | Logging Style Inconsistency: `_handle_state_changed()` uses f-string logging (`f"Error in state change handler: {e}"`) instead of Google-style docstring format consistent with codebase. | __init__.py:204 | Change to: `LOGGER.error("Error in state change handler: %s", e, exc_info=True)` to match established patterns. |
| MED-2 | Test Documentation Gap: Test for `test_unavailable_version_increments()` docstring says "on bulk_set" but story AC4 claims versioning works for all dataset changes. Test name should be `test_unavailable_version_increments_on_bulk_set()` for clarity, or test should cover both paths. | test_event_subscription.py:~line 293 | Clarify test purpose: rename to `test_unavailable_version_increments_on_bulk_set()` to indicate it's incomplete coverage, OR expand test to cover incremental operations. |

### 🟢 LOW Issues

| ID | Finding | File:Line | Resolution |
|----|---------|-----------|------------|
| LOW-1 | Code Organization: No comment separators between low_battery and unavailable sections make store.py harder to navigate. Both datasets have identical versioning bugs, suggesting copy-paste implementation without DRY refactoring. | store.py | Consider extracting shared dataset management logic into a helper class or parameterized methods to prevent future divergence. |

## Verification Commands

```bash
# Cannot run — pytest not installed in environment
# Expected commands:
pytest tests/ -v  # Should show 148 tests PASS
pytest tests/test_event_subscription.py::TestStateChangeEventHandling::test_unavailable_version_increments -v  # Verify version test
pytest tests/test_store.py -k "unavailable_version" -v  # Check all version-related tests
```

**Status: UNABLE TO VERIFY** — Pytest environment not configured. Story claims 148/148 tests pass, but cannot independently verify given the critical versioning bug exists in code.

## Summary of Issues

**Critical Assessment:**

This story claims AC4 (dataset versioning) is implemented and verified with 148 passing tests. However, a **critical architectural issue** exists:

- ✅ AC1, AC2, AC3 correctly implemented (unavailable detection, incremental updates, removal)
- ❌ **AC4 fundamentally broken** — versions only increment on `bulk_set()`, not on incremental `upsert()`/`remove()` called by state_changed events
- ❌ **Same issue affects low_battery dataset** — all incremental mutations lack version increments
- ❌ **Tests do not catch this** — `test_unavailable_version_increments()` only tests the bulk path, missing 99% of real-world mutations

**Impact:**
- Frontend cache invalidation (per ADR-002) will fail for state_changed events
- Only initial load and threshold changes will invalidate caches
- This is a production bug affecting real-time responsiveness

**Root Cause:**
Versioning was added only to `bulk_set_*()` methods, overlooking that state_changed event handler calls `upsert_*()` and `remove_*()` for incremental updates. This violates the event-driven architecture principle: every mutation should trigger cache invalidation.

**Resolution:**
Move version increment into `upsert_*()` and `remove_*()` methods to ensure all mutations are tracked. This should have been caught by the "AC4-Type Invariants" recommendation from Epic 2 retrospective, which explicitly noted: "Require both batch AND event handler test coverage from day 1."

