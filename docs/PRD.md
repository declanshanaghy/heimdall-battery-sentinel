# Product Requirements Document (PRD): Heimdall Battery Sentinel (Home Assistant)

**Version:** 1.2  
**Date:** 2026-02-19  
**Author:** BMAD Business Analyst (with Product Owner inputs)  
**Status:** Draft

## Document History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-02-19 | BA Agent | Initial PRD skeleton |
| 1.1 | 2026-02-19 | BA Agent | Updated with PO inputs: HA sidebar page, websocket-driven UI, low-battery + unavailable tables, HACS target |
| 1.2 | 2026-02-19 | BA Agent | Added PO decisions: configurable 15% threshold, battery entity selection rules, unavailable definition, sortable columns |

## 1. Introduction

### 1.1 Purpose
Define the MVP product requirements for **Heimdall Battery Sentinel**, a Home Assistant (HA) integration that provides a dedicated sidebar page to surface:
- **Low battery devices** (battery-class entities)
- **Unavailable devices** (any device_class)

This PRD is intended to be implementable by engineering and verifiable via end-user acceptance testing (UAT).

### 1.2 Scope
**In scope (MVP):**
- Home Assistant custom integration (backend) + frontend UI page linked in HA sidebar
- Discover and track devices/entities from HA
- Real-time UI updates driven by HA websocket events → backend state → frontend updates
- Two tables: low battery, unavailable devices
- Configurable low-battery threshold (default 15%) editable at setup and later
- Column sorting on both tables
- Robust handling of device/entity lifecycle (new, updated, removed) and edge cases

**Out of scope (MVP):**
- Notifications/alerts (Slack/email/SMS/etc.)
- Predictive analytics or battery life estimation
- HACS publishing automation (until after UAT)

### 1.3 References
- Product Owner inputs (this conversation)
- Home Assistant developer docs (websocket, integrations, frontend panels)

## 2. Product Overview

### 2.1 Product Vision
Provide a single, always-available **“battery and availability health”** view in Home Assistant that is:
- Fast to check (sidebar)
- Accurate and near-real-time
- Resilient to HA/device churn

### 2.2 Target Users
- Home Assistant power users managing many battery-powered sensors/devices
- Anyone wanting a quick “what needs attention” view without building custom dashboards

### 2.3 Success Metrics (MVP)
- **Correctness:** Table membership and row contents match HA device/entity state across updates, restarts, add/remove.
- **Latency:** UI row updates within **≤ 2 seconds** of state/device availability changes under normal HA load.
- **Completeness:** All devices with `device_class=battery` are considered for low-battery tracking.
- **Stability:** No runaway memory growth; cleanly handles event storms (many state changes).
- **Usability:** Sorting works consistently and indicates current sort order.

## 3. User Journeys

### UJ-1: View low battery devices
**Persona:** Home automation owner

1. User clicks **Heimdall Battery Sentinel** in the HA sidebar (MDI low-battery icon).
2. User sees a table of **low battery devices** with:
   - friendly name (link to the device page)
   - manufacturer & model
   - area
   - battery level
3. User clicks a device link and navigates to the HA device detail page to take action.

**Success criteria:**
- Low battery list is accurate.
- Links land on the correct device in HA.
- Sorting is available on all columns.

### UJ-2: View unavailable devices
**Persona:** Home automation owner

1. User opens the same sidebar page.
2. User sees a second table listing **unavailable devices** (any device_class).
3. User clicks a device link to troubleshoot.

**Success criteria:**
- Unavailable devices list is accurate and updates automatically when state changes.
- Sorting is available on all columns.

### UJ-3: Change threshold and see the page update
1. User edits the integration’s **low battery threshold** (default 15%) after setup.
2. Integration applies the new threshold.
3. The page updates (rows move in/out of low-battery table) without requiring a manual refresh.

**Success criteria:**
- Threshold can be changed at any time.
- UI updates to reflect the new rule.

### UJ-4: Real-time updates while page is open
1. A tracked device battery state changes (or becomes `unavailable` / recovers).
2. Backend receives relevant events from HA.
3. Backend updates internal state.
4. Backend pushes an update over websocket to the frontend.
5. Frontend finds the matching row (or creates/removes it) and updates the displayed values.

**Success criteria:**
- No full-page refresh required.
- Row is created/updated/removed in the correct table with correct data.

## 4. Functional Requirements

### 4.1 Navigation & UI surface (Home Assistant)
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-UI-001 | Integration provides a **sidebar entry** that opens the Battery Sentinel page | Must | Entry appears in sidebar after install/reload |
| FR-UI-002 | Sidebar icon uses an **MDI low-battery icon** | Must | Icon matches selected MDI low-battery glyph |
| FR-UI-003 | The page contains **two sections**: Low Battery Devices, Unavailable Devices | Must | Both sections render, even if empty |

### 4.2 Low Battery Devices table
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-LB-001 | The page lists all devices with at least one battery entity (`device_class=battery`) whose battery level is considered “low” | Must | Devices meeting criteria appear; others do not |
| FR-LB-002 | Low battery table columns are exactly: **Device Friendly Name**, **Manufacturer & Model**, **Area**, **Battery Level** | Must | Column headers and data present |
| FR-LB-003 | Device friendly name in table is a **link to the device** in HA Devices UI | Must | Clicking opens the correct HA device detail page |
| FR-LB-004 | Battery Level shows the selected battery value derived from HA state (see selection rules) | Must | Value matches HA state at time of render/update |
| FR-LB-005 | Battery selection rule (numeric): if device has multiple battery entities, pick one that reports a **number** (interpreted as percent remaining) | Must | Device shows percent from a numeric-reporting entity when available |
| FR-LB-006 | Battery selection rule (text): if device only has battery entities reporting textual levels (e.g., `low`/`medium`/`high`), treat **`low` as low-battery** and include the device when that battery entity state is `low` | Must | A `low` state appears in low-battery list; others do not |

**Notes / Clarifications:**
- Numeric battery states might be strings; implementation should coerce safely.
- If multiple numeric battery entities exist, selection priority is TBD (see Open Questions).

### 4.3 Unavailable Devices table
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-UNAV-001 | The page lists devices that are **unavailable** regardless of `device_class` | Must | Non-battery devices can appear |
| FR-UNAV-002 | Unavailable table columns are exactly: **Device Friendly Name**, **Manufacturer & Model**, **Area** | Must | Column headers and data present |
| FR-UNAV-003 | Device friendly name is a **link** to the HA device detail page | Must | Clicking opens correct device page |
| FR-UNAV-004 | Unavailable definition: an unavailable device is any device that has state=`unavailable` in Home Assistant | Must | List membership corresponds to HA’s unavailable state signals |

**Important note (implementation detail):**
Home Assistant generally represents `unavailable` at the **entity** state level. The integration must map entity state(s) to the device row. See Open Questions to lock the precise mapping.

### 4.4 Sorting
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-SORT-001 | All table headers are clickable to sort by that column | Must | Clicking a header sorts rows by that column |
| FR-SORT-002 | Repeated clicks on the same header alternate between ascending and descending | Must | Sort toggles asc/desc deterministically |
| FR-SORT-003 | Show an icon in the sorted column header indicating current sort direction | Must | Icon is visible and updates when direction changes |
| FR-SORT-004 | Sorting applies independently to each table | Should | Sorting low-battery doesn’t affect unavailable (and vice versa) |

### 4.5 Low-battery threshold configuration
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-THR-001 | Default low-battery threshold is **15%** | Must | Fresh install uses 15% |
| FR-THR-002 | During integration setup, user can configure the threshold | Must | Config flow includes threshold input |
| FR-THR-003 | User can edit the threshold at any time after setup | Must | Options flow (or equivalent) updates stored value |
| FR-THR-004 | Changing threshold updates UI list membership without manual refresh | Must | Rows move in/out appropriately |

### 4.6 Data sourcing: Home Assistant websocket
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-WS-001 | Frontend page reads all data from Home Assistant via the **Home Assistant websocket service** | Must | No REST polling required for normal operation |
| FR-WS-002 | Backend subscribes to relevant HA events to receive device/entity updates | Must | Updates arrive for state changes, new devices, removed devices |
| FR-WS-003 | On receiving a tracked device update, backend updates internal state and emits an update message to the frontend over websocket | Must | Frontend updates specific row without full reload |
| FR-WS-004 | Events can include **new devices** and **removed devices**; system handles both gracefully | Must | New devices appear when they meet criteria; removed devices disappear |

### 4.7 Edge cases & correctness
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-EDGE-001 | If a device moves between categories (battery recovers, becomes unavailable, etc.), row moves to/from the correct table | Must | Row appears in correct table(s) per defined logic |
| FR-EDGE-002 | If required metadata is missing (manufacturer/model/area), UI shows a safe placeholder (e.g., “—”) and continues | Must | No crashes; row renders |
| FR-EDGE-003 | On HA restart / integration reload, internal state is rebuilt and UI shows correct current state | Must | After restart, tables reflect reality |
| FR-EDGE-004 | If frontend connects late, it receives a full initial snapshot plus incremental updates afterward | Must | UI is correct even if page opened later |

## 5. Non-Functional Requirements

### 5.1 Performance
| ID | Requirement |
|---|---|
| NFR-PERF-001 | UI updates propagate within **≤ 2 seconds** from HA change to visible row update (typical LAN HA installs) |
| NFR-PERF-002 | Integration must handle at least **500 devices / 2000 entities** without excessive CPU usage or UI lag |

### 5.2 Reliability & Resilience
| ID | Requirement |
|---|---|
| NFR-REL-001 | Integration must tolerate event storms (many state changes) without losing correctness |
| NFR-REL-002 | Websocket reconnects are handled (frontend/back-end) and state resync occurs |

### 5.3 Security & Privacy
| ID | Requirement |
|---|---|
| NFR-SEC-001 | Use HA’s existing authentication/session model; do not introduce new external network services |
| NFR-SEC-002 | No telemetry is sent outside the HA instance in MVP |

### 5.4 Compatibility
| ID | Requirement |
|---|---|
| NFR-COMP-001 | Integration is compatible with HACS packaging conventions (even if publishing is deferred) |

## 6. Data Model (Conceptual)

### 6.1 Entities (internal state)
This is conceptual; implementation may vary.

#### DeviceRecord
- `device_id` (string)
- `friendly_name` (string)
- `manufacturer` (string|null)
- `model` (string|null)
- `area` (string|null)
- `is_unavailable` (bool)
- `battery_level` (number|string|null)
- `battery_entity_id` (string|null) — chosen battery entity for display
- `battery_entity_ids` (list)
- `last_updated` (timestamp)

### 6.2 Derived sets
- `low_battery_devices`:
  - numeric case: devices where `battery_level <= threshold_percent`
  - textual case: devices where chosen battery level state == `low`
- `unavailable_devices`: devices where `is_unavailable == true` (per mapping rules)

## 7. Interface / API Overview

### 7.1 Frontend ↔ Backend messaging (websocket)
The frontend expects:
- An **initial snapshot** message containing the full computed tables
- **Incremental update** messages keyed by `device_id` to update/move/remove a row

Suggested message types:
- `snapshot`: `{ threshold_percent, sort_state, low_battery: DeviceRow[], unavailable: DeviceRow[] }`
- `device_upsert`: `{ device_id, row, table: 'low_battery'|'unavailable'|'none' }`
- `device_remove`: `{ device_id }`
- `threshold_update`: `{ threshold_percent }`

### 7.2 Links to HA Device UI
Requirement: device name links to the HA Devices page for that device.

Implementation detail depends on HA frontend routing conventions; validate during UAT.

## 8. Deployment & Release

### 8.1 Distribution target
- Target: **HACS** (Home Assistant Community Store)
- HACS publishing/setup is **deferred until after final UAT**

### 8.2 Development/UAT flow
- Install/publish the integration directly to Dek’s HA server during development
- Iterate until end-user acceptance
- After acceptance: set up HACS packaging/release mechanics

## 9. Out of Scope
- Alerts/notifications
- Predictive analytics
- Historical reporting

## 10. Key Decisions
- Track all devices in Home Assistant that have an entity with `device_class=battery` for battery monitoring.
- Default low-battery threshold is **15%**, and is **configurable** during setup and after setup.
- Devices with multiple battery entities: choose one reporting a **numeric percent** when possible.
- If battery entities only report `low/medium/high`, treat `low` as the low-battery threshold.
- “Unavailable devices” are devices associated with entity states reporting `unavailable` (exact mapping to be confirmed).
- Primary UI is a sidebar-linked page with an MDI low-battery icon.
- UI shows two tables: low batteries (battery-class) and unavailable devices (any device_class).
- All table headers are clickable for sorting with asc/desc toggle and a direction icon.
- Frontend reads via Home Assistant websocket; backend subscribes to HA events, maintains internal state, and pushes updates to frontend.
- Target distribution is HACS, but publishing setup is delayed until after UAT.

## 11. Assumptions
- Battery levels are available as numeric-like states (often percentage) for many battery-class entities.
- HA websocket APIs provide sufficient event data to maintain accurate state.
- HA’s UI routing allows linking to a specific device detail view.

## 12. Open Questions
| # | Question | Owner | Status |
|---:|---|---|---|
| 1 | Threshold constraints: allowed range and step? (e.g., 1–100, step 1) | Product Owner | Open |
| 2 | If multiple numeric battery entities exist: which to select (min? first found? prefer `sensor.*battery*`?) | Product Owner | Open |
| 3 | For textual battery levels: are there other vocabularies besides `low/medium/high`? (e.g., `critical`) | Product Owner | Open |
| 4 | Unavailable mapping: does a device enter the Unavailable table if **any** entity for that device is `unavailable`, or only if **all** entities are `unavailable`? | Product Owner | Open |
| 5 | Sorting: what is the default sort when the page loads? (e.g., battery ascending so lowest first) | Product Owner | Open |
| 6 | Sorting: should sort be stable (secondary sort by name) when values tie? | Product Owner | Open |
| 7 | Battery value display: do you want percent symbol and rounding rules (e.g., 14.7 → 15)? | Product Owner | Open |
| 8 | Unavailable table membership for devices without a device registry entry (entity-only): should they appear? | Product Owner | Open |
| 9 | Should the UI expose a manual “refresh/resync” button, or rely on websocket + reconnect only? | Product Owner | Open |

## 13. Glossary
| Term | Definition |
|---|---|
| HA | Home Assistant |
| HACS | Home Assistant Community Store |
| Device | Home Assistant device registry entry |
| Entity | Home Assistant entity (sensor, binary_sensor, etc.) |
| device_class=battery | Entity classification indicating battery status/level |
| Unavailable | HA state indicating entity/device is not currently available |
