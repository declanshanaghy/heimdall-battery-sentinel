# Product Requirements Document (PRD): Heimdall Battery Sentinel (Home Assistant)

**Version:** 1.1  
**Date:** 2026-02-19  
**Author:** BMAD Business Analyst (with Product Owner inputs)  
**Status:** Draft

## Document History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-02-19 | BA Agent | Initial PRD skeleton |
| 1.1 | 2026-02-19 | BA Agent | Updated with PO inputs: HA sidebar page, websocket-driven UI, low-battery + unavailable tables, HACS target |

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
- Low battery list is accurate and sortable/readable.
- Links land on the correct device in HA.

### UJ-2: View unavailable devices
**Persona:** Home automation owner

1. User opens the same sidebar page.
2. User sees a second table listing **unavailable devices** (any device_class).
3. User clicks a device link to troubleshoot.

**Success criteria:**
- Unavailable devices list is accurate and updates automatically when availability changes.

### UJ-3: Real-time updates while page is open
1. A device battery state changes (or device becomes unavailable/available).
2. Backend receives device/entity update events from HA.
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
| FR-UI-002 | Sidebar icon uses **Material Design Icons** “low battery” icon | Must | Icon matches selected MDI low-battery glyph |
| FR-UI-003 | The page contains **two sections**: Low Battery Devices, Unavailable Devices | Must | Both sections render, even if empty |

### 4.2 Low Battery Devices table
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-LB-001 | The page lists all devices with at least one battery entity (`device_class=battery`) whose battery level is considered “low” | Must | Devices meeting criteria appear; others do not |
| FR-LB-002 | Low battery table columns are exactly: **Device Friendly Name**, **Manufacturer & Model**, **Area**, **Battery Level** | Must | Column headers and data present |
| FR-LB-003 | Device friendly name in table is a **link to the device** in HA Devices UI | Must | Clicking opens the correct HA device detail page |
| FR-LB-004 | Battery Level shows current battery percentage (or value) derived from HA state for the battery entity | Must | Value matches HA state at time of render/update |

**Notes / Clarifications (needs finalization):**
- Define what “low” means (threshold). See Open Questions.
- Devices with multiple battery entities: define which value to display (min? primary? show best/most recent?). See Open Questions.

### 4.3 Unavailable Devices table
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-UNAV-001 | The page lists devices that are **unavailable** regardless of `device_class` | Must | Non-battery devices can appear |
| FR-UNAV-002 | Unavailable table columns are exactly: **Device Friendly Name**, **Manufacturer & Model**, **Area** | Must | Column headers and data present |
| FR-UNAV-003 | Device friendly name is a **link** to the HA device detail page | Must | Clicking opens correct device page |

### 4.4 Data sourcing: Home Assistant websocket
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-WS-001 | Frontend page reads all data from Home Assistant via the **Home Assistant websocket service** | Must | No REST polling required for normal operation |
| FR-WS-002 | Backend subscribes to relevant HA events to receive device/entity updates | Must | Updates arrive for state changes, new devices, removed devices |
| FR-WS-003 | On receiving a tracked device update, backend updates internal state and emits an update message to the frontend over websocket | Must | Frontend updates specific row without full reload |
| FR-WS-004 | Events can include **new devices** and **removed devices**; system handles both gracefully | Must | New devices appear when they meet criteria; removed devices disappear |

### 4.5 Edge cases & correctness
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-EDGE-001 | If a device moves between categories (e.g., becomes unavailable, battery recovers), row moves to/from the correct table | Must | Row appears in exactly one applicable table |
| FR-EDGE-002 | If required metadata is missing (manufacturer/model/area), UI shows a safe placeholder (e.g., “—”) and continues | Must | No crashes; row renders |
| FR-EDGE-003 | On HA restart / integration reload, internal state is rebuilt and UI shows correct current state | Must | After restart, tables reflect reality |
| FR-EDGE-004 | If frontend connects late, it receives a full initial snapshot plus incremental updates afterward | Must | UI is correct even if page opened hours later |

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
- `battery_entity_ids` (list)
- `last_updated` (timestamp)

### 6.2 Derived sets
- `low_battery_devices`: devices where `battery_level <= threshold` (definition TBD)
- `unavailable_devices`: devices where `is_unavailable == true` (definition TBD: device vs entity availability)

## 7. Interface / API Overview

### 7.1 Frontend ↔ Backend messaging (websocket)
The frontend expects:
- An **initial snapshot** message containing the full computed tables
- **Incremental update** messages keyed by `device_id` to update/move/remove a row

Suggested message types:
- `snapshot`: `{ low_battery: DeviceRow[], unavailable: DeviceRow[] }`
- `device_upsert`: `{ device_id, row, table: 'low_battery'|'unavailable'|'none' }`
- `device_remove`: `{ device_id }`

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
- Track **all devices in Home Assistant** that have an entity with `device_class=battery` for battery monitoring.
- Primary UI is a **sidebar-linked page** with an **MDI low-battery icon**.
- UI shows **two tables**: low batteries (battery-class) and unavailable devices (any device_class).
- **Frontend reads via Home Assistant websocket**.
- **Backend receives device/entity events** from Home Assistant, maintains internal state, and pushes updates to frontend.
- Target distribution is **HACS**, but publishing setup is delayed until after UAT.

## 11. Assumptions
- Battery levels are available as numeric-like states (often percentage) for battery-class entities.
- HA websocket APIs provide sufficient event data to maintain accurate state.
- “Device unavailable” can be derived from HA’s concepts (device availability and/or all entities unavailable). Exact definition to confirm.

## 12. Open Questions
| # | Question | Owner | Status |
|---:|---|---|---|
| 1 | What is the **low battery threshold**? (e.g., <= 20%) Should it be configurable? | Product Owner | Open |
| 2 | How to compute **battery_level per device** if multiple battery entities exist? (min, max, primary, or list) | Product Owner | Open |
| 3 | Exact definition of **unavailable device**: device registry availability vs entity state == `unavailable` vs integration-level availability? | Product Owner | Open |
| 4 | Should the tables support sorting/filtering in MVP (by area, battery %, etc.)? | Product Owner | Open |
| 5 | Preferred behavior for `unknown`/non-numeric battery states (ignore, show “—”, treat as low?) | Product Owner | Open |

## 13. Glossary
| Term | Definition |
|---|---|
| HA | Home Assistant |
| HACS | Home Assistant Community Store |
| Device | Home Assistant device registry entry |
| Entity | Home Assistant entity (sensor, binary_sensor, etc.) |
| device_class=battery | Entity classification indicating battery status/level |
| Unavailable | HA state indicating entity/device is not currently available |
