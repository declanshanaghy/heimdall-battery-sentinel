# Story 2-1: Numeric Battery Evaluation

## Purpose
Implement core battery monitoring for numeric battery entities meeting Home Assistant integration standards. This story focuses on detecting low battery levels for entities that report percentage values, excluding mobile device batteries. The implementation will provide server-side paging and sorting capabilities.

## Acceptance Criteria
- ✅ Monitor entities with device_class=battery AND unit_of_measurement='%'
- ✅ Default threshold at 15% (configurable)
- ✅ Display battery level as rounded integer with '%' sign (e.g., 14.7% → 15%)
- ✅ For devices with multiple battery entities, select the first by entity_id ascending
- ✅ Server-side paging/sorting of battery entities with page size=100
- ❌ Exclude mobile device batteries (BatteryManager API)
- ❌ Handle entities without unit_of_measurement or with non-percentage units

## Dev Notes
- Threshold will be stored in config entry options (constant for now)
- Use device registry to resolve one battery per device
- Battery evaluation: 
  - Parse state as number 
  - Check unit_of_measurement == "%"
  - Include if value <= threshold
- Display rounded integer value with '%' suffix
- Server-side sorting required for large datasets (FR-SORT-006)

### References
- Source: epics.md#2.1
- Source: prd.md#FR-LB-004,FR-LB-005,FR-LB-006
- Source: architecture.md#ADR-005
- Source: architecture.md#ADR-004 (server-side sorting)
