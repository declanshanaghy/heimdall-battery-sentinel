# Code Review Report

**Story:** 2-1-numeric-battery
**Reviewer:** minimax-m2.5
**Date:** 2026-02-21
**Overall Verdict:** CHANGES_REQUESTED

## Prior Epic Recommendations

| Recommendation | Source Epic | Status |
|---------------|-------------|--------|
| Documentation Drift: File List should match git reality | Epic 1 | ✅ Followed |
| Redundant notification path causes duplicate messages | Epic 1 | ✅ Not Applicable |

## Checklist Verification

- [x] Story file loaded and parsed
- [x] Story status verified as reviewable (was: review)
- [x] Acceptance Criteria cross-checked against implementation
- [x] File List reviewed and validated for completeness
- [x] Code quality review performed on changed files
- [x] Security review performed
- [x] Tests verified to exist and pass

## Acceptance Criteria Validation

| AC | Status | Evidence |
|----|--------|----------|
| AC1: Monitor entities with device_class=battery AND unit_of_measurement='%' | PASS | evaluator.py:evaluate_numeric_battery checks unit == "%" |
| AC2: Default threshold at 15% (configurable) | PASS | store.py:Store.threshold defaults to 15 |
| AC3: Display battery level as rounded integer with '%' sign | PASS | evaluator.py:evaluate_battery returns rounded display |
| AC4: For devices with multiple battery entities, select first by entity_id ascending | **FAIL** | **NOT IMPLEMENTED - no logic in __init__.py or registry.py to filter by device** |
| AC5: Server-side paging/sorting with page size=100 | PASS | store.py:get_paginated() with PaginatedResult |
| AC6: Exclude mobile device batteries | N/A | Explicitly out of scope (marked ❌) |
| AC7: Handle entities without unit_of_measurement or non-percentage units | PASS | evaluator.py returns not low for wrong/no unit |

## Findings

### 🔴 CRITICAL Issues

| ID | Finding | File:Line | Resolution |
|----|---------|-----------|------------|
| CRIT-1 | AC #4 "For devices with multiple battery entities, select the first by entity_id ascending" is marked complete in story but NOT implemented | Story file marker's false claim | Add logic to filter to first battery entity per device in __init__.py:_update_low_battery_store() |

### 🟠 HIGH Issues

*None*

### 🟡 MEDIUM Issues

*None*

### 🟢 LOW Issues

*None*

## Verification Commands

```bash
python -m pytest tests/ -v  # PASS - 58 tests passed
```

## Required Actions

1. Implement device-level battery deduplication: for devices with multiple battery entities, keep only the one with lowest entity_id (ascending)
2. This requires tracking device_id -> first_battery_entity_id mapping in the store or registry
3. Re-run tests after implementation

---

**Note:** All other acceptance criteria are properly implemented. The paging and sorting implementation is solid with proper tie-breaker logic. Tests are comprehensive and all pass.
