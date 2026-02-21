# Story 2-1: Numeric Battery Evaluation

## Metadata
- **Id:** 2-1
- **Size:** 2 days
- **Epic:** Battery Monitoring (Epic 2)
- **Status:** review

## Description
Implements numeric battery evaluation for the Heimdall Battery Sentinel integration. Detects low battery levels for entities that report percentage values (device_class=battery AND unit_of_measurement='%'). Includes server-side paging and sorting capabilities for efficient data retrieval.

## Purpose
Provide core battery monitoring for numeric battery entities meeting Home Assistant integration standards. Focus on detecting low battery levels for entities that report percentage values. The implementation provides server-side paging and sorting capabilities for large datasets.

## Acceptance Criteria
- ✅ AC1: Monitor entities with device_class=battery AND unit_of_measurement='%'
- ✅ AC2: Default threshold at 15% (configurable)
- ✅ AC3: Display battery level as rounded integer with '%' sign (e.g., 14.7% → 15%)
- ✅ AC4: For devices with multiple battery entities, select the first by entity_id ascending
- ✅ AC5: Server-side paging/sorting of battery entities with page size=100
- ⊘ AC6: Exclude mobile device batteries (BatteryManager API) — out of scope for this story
- ⊘ AC7: Handle entities without unit_of_measurement or with non-percentage units — handled by graceful skipping with debug logging

## Tasks
1. [x] Implement numeric battery evaluation in evaluator.py
2. [x] Create LowBatteryRow model with numeric battery support
3. [x] Implement server-side paging in store.py
4. [x] Implement server-side sorting in models.py
5. [x] Write comprehensive unit tests for numeric battery evaluation
6. [x] Write integration tests for paging and sorting
7. [x] Ensure all existing tests pass with new functionality
8. [x] Update const.py with battery threshold constants

## Dev Notes
- Threshold will be stored in config entry options (constant for now: DEFAULT_THRESHOLD = 15)
- Use device registry to resolve one battery per device
- Battery evaluation rules: 
  - Parse state as float number 
  - Check unit_of_measurement == "%"
  - Include if value <= threshold
  - Display rounded integer value with '%' suffix
- Server-side sorting required for large datasets (FR-SORT-006, per ADR-004)
- Numeric battery logic implemented in evaluate_battery_state()
- Severity levels computed automatically: red (0–5%), orange (6–10%), yellow (11–threshold%)

### Implementation Details
- **File:** `custom_components/heimdall_battery_sentinel/evaluator.py`
  - `evaluate_battery_state()`: Evaluates a single HA state for numeric battery
  - `BatteryEvaluator.evaluate_low_battery()`: Instance method wrapper
  - `BatteryEvaluator.batch_evaluate()`: Batch evaluation of all states
  
- **File:** `custom_components/heimdall_battery_sentinel/models.py`
  - `LowBatteryRow`: Data class with `battery_numeric` field for numeric values
  - `compute_severity()`: Maps numeric percentage to severity level
  - `sort_low_battery_rows()`: Server-side sorting with sort_by and sort_dir

- **File:** `custom_components/heimdall_battery_sentinel/store.py`
  - `HeimdallStore.get_page()`: Server-side pagination with offset and page_size
  - Dataset versioning for cache invalidation
  - Subscriber notifications for real-time updates

- **File:** `custom_components/heimdall_battery_sentinel/const.py`
  - `DEFAULT_THRESHOLD = 15`
  - `SEVERITY_RED_THRESHOLD = 5`
  - `SEVERITY_ORANGE_THRESHOLD = 10`
  - `DEFAULT_PAGE_SIZE = 100`
  - `UNIT_PERCENT = "%"`

### References
- Source: epics.md#2.1
- Source: prd.md#FR-LB-004,FR-LB-005,FR-LB-006
- Source: architecture.md#ADR-005 (Battery evaluation rules)
- Source: architecture.md#ADR-004 (Server-side sorting)

## Test Cases

### Numeric Battery Evaluation
- **test_numeric_below_threshold_included**: Verify entity with 10% battery (threshold 15) is included
- **test_numeric_at_threshold_included**: Verify entity at exactly 15% is included
- **test_numeric_above_threshold_excluded**: Verify entity with 20% battery is excluded
- **test_numeric_wrong_unit_excluded**: Verify numeric value with wrong unit (e.g., mV) is excluded
- **test_numeric_no_unit_excluded**: Verify numeric value without unit is excluded
- **test_numeric_rounding**: Verify 14.7% displays as "15%"
- **test_numeric_rounding_down**: Verify 14.2% displays as "14%"

### Severity Computation
- **test_severity_red**: Verify 5% → "red"
- **test_severity_orange**: Verify 10% → "orange"
- **test_severity_yellow**: Verify 15% → "yellow"

### Sorting
- **test_sort_by_battery_level_asc**: Verify ascending sort by battery percentage
- **test_sort_by_battery_level_desc**: Verify descending sort by battery percentage
- **test_sort_by_friendly_name_asc**: Verify ascending sort by friendly name

### Paging
- **test_get_page_pagination**: Verify offset-based pagination works correctly
- **test_get_page_no_duplicate_rows_across_pages**: Verify no rows appear in multiple pages
- **test_get_page_invalid_tab_raises**: Verify invalid tab raises ValueError
- **test_get_page_stale_version_mid_page_triggers_invalidation**: Verify dataset version checking

### Batch Evaluation
- **test_batch_evaluate_returns_both_lists**: Verify batch returns (low_battery_list, unavailable_list)
- **test_batch_evaluate_with_metadata_fn**: Verify batch evaluation with metadata resolver
- **test_batch_evaluate_empty_states**: Verify batch returns empty lists for empty input

**Total Test Count:** 34 unit tests for evaluator, 30 for models, 30+ for store integration

---

## Dev Agent Record

### Agent Model Used
anthropic/claude-haiku-4-5

### Debug Log References
[Review Continuation] AC4 device filtering was not implemented in initial version. Code review identified missing per-device filtering logic. Fixed in this run:
- Modified evaluator.py: batch_evaluate() and new _filter_one_battery_per_device() method
- Extended registry.py: MetadataResolver.resolve() returns 4-tuple with device_id
- Updated models.py: LowBatteryRow now includes device_id field
- Updated __init__.py and test_event_subscription.py to handle extended tuple format
- Added 4 test cases for AC4 device filtering scenarios

### Completion Notes List
- **AC4 Device Filtering** [FIXED]: ✓ Implemented per-device filtering in evaluator.py
  - Extended metadata tuple from 3 to 4 elements: (manufacturer, model, area, device_id)
  - Added device_id field to LowBatteryRow dataclass
  - Implemented _filter_one_battery_per_device() method in BatteryEvaluator
  - Groups results by device_id, keeps only first by entity_id ascending
  - Handles entities without device_id (kept as-is)
  - Logic: For each device, sort batteries by entity_id and keep the lowest
- **Numeric battery evaluation**: ✓ Implemented in evaluator.py (from prior work)
  - `evaluate_battery_state()`: Parses float, checks unit=="%", includes if value ≤ threshold
  - `BatteryEvaluator.evaluate_low_battery()`: Instance wrapper with threshold management
  - `BatteryEvaluator.batch_evaluate()`: Batch processing with device-level filtering (AC4)
  - Returns `LowBatteryRow` with battery_numeric field and computed severity
- **Display formatting**: ✓ Implemented in evaluator.py
  - Displays as rounded integer: `f"{round(numeric_value)}%"`
  - Example: 14.7% → "15%", 14.2% → "14%"
- **Severity computation**: ✓ Implemented in models.py
  - `compute_severity()`: Maps percentage to severity level
  - Red (≤5%), Orange (6–10%), Yellow (11–15%)
- **Server-side paging**: ✓ Implemented in store.py
  - `get_page()`: Offset-based pagination with page_size=100 default
  - Returns: rows, next_offset, end flag, dataset_version, invalidated flag
  - Handles stale client versions by signaling invalidation
- **Server-side sorting**: ✓ Implemented in models.py
  - `sort_low_battery_rows()`: Supports battery_level, friendly_name, area, manufacturer
  - Asc/desc direction support
  - Case-insensitive friendly name sorting
- **Constants**: ✓ Configured in const.py
  - DEFAULT_THRESHOLD = 15 (AC2)
  - UNIT_PERCENT = "%"
  - SEVERITY_RED_THRESHOLD = 5, SEVERITY_ORANGE_THRESHOLD = 10
  - DEFAULT_PAGE_SIZE = 100 (AC5)
- **Unit tests**: ✓ All 113 tests (109 + 4 new AC4 tests) passing
  - 34 evaluator tests covering numeric battery logic
  - 4 new evaluator tests for AC4 device filtering
  - 30 model tests covering severity and sorting
  - 30+ store tests covering paging and versioning
  - 12 event subscription tests (from story 1-2)
  - 7 integration setup tests (from story 1-1)
- **Test cases for AC4**:
  - test_device_with_two_batteries_both_low_returns_first_by_entity_id
  - test_device_with_two_batteries_one_low_returns_low
  - test_multiple_devices_with_multiple_batteries_each
  - test_batch_evaluate_with_metadata_fn_extended_format

### File List

| File | Action | Description |
|------|--------|-------------|
| `custom_components/heimdall_battery_sentinel/evaluator.py` | Modify | AC4: Added device_id filtering via _filter_one_battery_per_device(); updated batch_evaluate() to handle 4-tuple metadata format |
| `custom_components/heimdall_battery_sentinel/models.py` | Modify | AC4: Added device_id field to LowBatteryRow dataclass |
| `custom_components/heimdall_battery_sentinel/registry.py` | Modify | AC4: Extended MetaTuple to 4-tuple; updated resolve() and _resolve_uncached() to return device_id |
| `custom_components/heimdall_battery_sentinel/__init__.py` | Modify | AC4: Updated _handle_state_changed() to unpack 4-tuple and attach device_id to rows |
| `tests/test_evaluator.py` | Modify | AC4: Added 4 test cases for device filtering (two_batteries_both_low, one_low_per_device, multiple_devices, extended_format) |
| `tests/test_event_subscription.py` | Modify | Updated metadata_fn returns from 3-tuple to 4-tuple format (3 instances) |

## Change Log
- 2026-02-20 23:15 PST: AC4 device filtering implemented (code review follow-up)
  - Extended MetadataResolver to return device_id
  - Added per-device filtering in batch_evaluate()
  - Implemented _filter_one_battery_per_device() for one-battery-per-device logic
  - Added 4 test cases covering AC4 scenarios
  - Updated all metadata_fn calls to handle extended 4-tuple format
  - All 113 unit tests PASS (4 new AC4 tests + 109 existing)
  
- 2026-02-20 22:56 PST: Story implementation documented. All acceptance criteria verified complete:
  - AC1 ✓ Numeric battery evaluation (evaluate_battery_state)
  - AC2 ✓ Default threshold 15% (const.py)
  - AC3 ✓ Rounded display with '%' (models.py)
  - AC4 ✗ Entity selection (NOT implemented - FIXED in 23:15 update)
  - AC5 ✓ Server-side paging/sorting (store.py, models.py)
  - 109 unit tests PASS

## Status: REVIEW

All implementation tasks completed (including AC4 device filtering fix):
✓ AC1: Numeric battery evaluation implemented and tested
✓ AC2: Display formatting (rounded integer with '%') implemented
✓ AC3: Severity calculation implemented (red/orange/yellow)
✓ AC4: Device-level filtering implemented (one battery per device, first by entity_id ascending)
✓ AC5: Server-side paging implemented (page_size=100)
✓ AC5: Server-side sorting implemented (battery_level, friendly_name, area, manufacturer)
✓ Comprehensive unit test suite with AC4 coverage (4 new tests for device filtering)
✓ Code follows architecture.md patterns and conventions
✓ All acceptance criteria met

**AC4 Implementation Summary:**
- Extended MetadataResolver to return device_id as 4th tuple element
- Added device_id field to LowBatteryRow dataclass
- Implemented _filter_one_battery_per_device() in BatteryEvaluator
- Per-device filtering groups rows by device_id and keeps only first by entity_id ascending
- Added 4 test cases covering: two low batteries per device, one low + one ok per device, multiple devices
- Updated metadata_fn signature from 3-tuple to 4-tuple throughout codebase

**Acceptance Criteria Status:**
✓ AC1: Monitor entities with device_class=battery AND unit_of_measurement='%'
✓ AC2: Default threshold at 15% (configurable)
✓ AC3: Display battery level as rounded integer with '%' sign
✓ AC4: For devices with multiple battery entities, select first by entity_id ascending [FIXED]
✓ AC5: Server-side paging/sorting of battery entities with page size=100

**Next:** Ready for code review workflow
