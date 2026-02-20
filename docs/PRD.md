# Product Requirements Document (PRD): Heimdall Battery Sentinel (Home Assistant)

**Version:** 1.4  
**Date:** 2026-02-19  
**Author:** BMAD Business Analyst (with Product Owner inputs)  
**Status:** Draft

## Document History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-02-19 | BA Agent | Initial PRD skeleton |
| 1.1 | 2026-02-19 | BA Agent | Updated with PO inputs: HA sidebar page, websocket-driven UI, low-battery + unavailable tables, HACS target |
| 1.2 | 2026-02-19 | BA Agent | Added PO decisions: configurable 15% threshold, battery selection rules, unavailable definition, sortable columns |
| 1.3 | 2026-02-19 | BA Agent | Shifted to entity-first model (low batteries + unavailable); threshold slider step=5; default sorts; rounding/%; row color coding; theme |
| 1.4 | 2026-02-19 | BA Agent | Locked threshold range (5–100); link to entity page; accept only % units; include all unavailable; add delete-entity action; add tabs + infinite scroll; add severity icons |

## 1. Introduction

### 1.1 Purpose
Define the MVP product requirements for **Heimdall Battery Sentinel**, a Home Assistant (HA) integration that provides a dedicated sidebar page to surface:
- **Low battery entities** (entities with `device_class=battery`)
- **Unavailable entities** (any domain / any device_class)

This PRD is intended to be implementable by engineering and verifiable via end-user acceptance testing (UAT).

### 1.2 Scope
**In scope (MVP):**
- Home Assistant custom integration (backend) + frontend UI page linked in HA sidebar
- Discover and track entities from HA
- Real-time UI updates driven by HA websocket events → backend state → frontend updates
- UI uses **two tabs** within a single page:
  - Low Battery
  - Unavailable
- Each tab presents a sortable, infinitely scrollable table (incremental loading as user scrolls)
- Configurable low-battery threshold (default 15%) editable at setup and later
- Low-battery row color coding and severity icon
- Unavailable table includes an action to delete an entity from the entity registry
- Robust handling of entity lifecycle (new, updated, removed) and edge cases

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
- Resilient to HA/entity churn

### 2.2 Target Users
- Home Assistant power users managing many battery-powered sensors/devices

### 2.3 Success Metrics (MVP)
- **Correctness:** Table membership and row contents match HA entity state across updates, restarts, add/remove.
- **Latency:** UI row updates within **≤ 2 seconds** of entity state changes under normal HA load.
- **Completeness:** All entities with `device_class=battery` are considered for low-battery tracking (but only numeric `%` entities count for percent thresholding).
- **Stability:** No runaway memory growth; cleanly handles event storms (many state changes).
- **Usability:** Sorting works consistently, indicates sort direction, and feels stable even with infinite scroll.

## 3. User Journeys

### UJ-1: View low battery entities
1. User clicks **Heimdall Battery Sentinel** in the HA sidebar.
2. User lands on the page and opens the **Low Battery** tab.
3. User sees a table of low battery entities and scrolls to load more.
4. User clicks an entity name to open the entity page.

### UJ-2: View unavailable entities
1. User opens the **Unavailable** tab.
2. User sees a table of all entities currently `unavailable`.
3. User optionally deletes a broken/stale entity from the registry.

### UJ-3: Change threshold and see the page update
1. User edits the integration’s low battery threshold.
2. Integration applies the new threshold.
3. Low-battery tab updates (rows move in/out; severity indicators update) without manual refresh.

## 4. Functional Requirements

### 4.1 Navigation, look & feel
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-UI-001 | Integration provides a **sidebar entry** that opens the Battery Sentinel page | Must | Entry appears in sidebar after install/reload |
| FR-UI-002 | Sidebar icon uses an **MDI low-battery icon** | Must | Icon matches selected MDI low-battery glyph |
| FR-UI-003 | The page uses **two tabs**: Low Battery, Unavailable | Must | Tabs render; switching tabs works |
| FR-UI-004 | Page uses the **Home Assistant default theme** / user’s preferred theme | Must | Styling respects HA theme variables |

### 4.2 Low Battery table (entity-based)
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-LB-001 | The Low Battery tab lists entities with `device_class=battery` that are considered “low” | Must | Entities meeting criteria appear |
| FR-LB-002 | Low battery table headers are: **Friendly Name**, **Manufacturer & Model**, **Area**, **Battery Level** | Must | Column headers and data present |
| FR-LB-003 | Friendly Name links to the **entity page** in Home Assistant | Must | Clicking opens the correct entity page |
| FR-LB-004 | Numeric Battery Level is shown as a rounded integer percent with a `%` suffix | Must | e.g., `14.7` → `15%` |
| FR-LB-005 | Numeric eligibility: only accept numeric battery states when the unit is exactly `%` | Must | Numeric non-% units (e.g., V) are not treated as percent batteries |
| FR-LB-006 | Battery selection: assume no device has >1 numeric % battery entity; pick the first one found | Must | Selection deterministic |
| FR-LB-007 | Textual batteries: support only `low/medium/high`; treat `low` as low-battery | Must | `low` included; others not |

### 4.3 Low-battery severity (color + icon)
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-SEV-001 | Low-battery rows are color-coded by severity relative to threshold | Must | Color bands match rule |
| FR-SEV-002 | Add a severity icon (MDI) in the row (or Battery Level cell) indicating severity | Must | Icon changes with severity |

**Severity rule (numeric batteries only):**
- Let `T` = threshold percent (default 15)
- Let `B` = battery percent
- Include entity when `B <= T`
- Compute `ratio = (B / T) * 100`
  - `0..33` → red + most severe icon
  - `34..66` → orange + medium severity icon
  - `67..100` → yellow + least severe icon

(Exact MDI icon choices are implementation detail; must be “most appropriate.”)

### 4.4 Unavailable table (entity-based)
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-UNAV-001 | The Unavailable tab lists **all entities** whose state is exactly `unavailable` | Must | Unavailable entities appear even if metadata is empty |
| FR-UNAV-002 | Unavailable table headers are: **Friendly Name**, **Manufacturer & Model**, **Area**, **Actions** | Must | Column headers and data present |
| FR-UNAV-003 | Friendly Name links to the **entity page** in Home Assistant | Must | Clicking opens correct destination |
| FR-UNAV-004 | Actions column includes a button to **delete the entity from the entity registry** | Must | Delete triggers registry removal flow |
| FR-UNAV-005 | Delete requires confirmation to prevent accidental removal | Must | Confirmation dialog/step exists |

### 4.5 Sorting
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-SORT-001 | All table headers are clickable to sort by that column | Must | Clicking sorts |
| FR-SORT-002 | Repeated clicks alternate asc/desc | Must | Deterministic |
| FR-SORT-003 | Sorted header shows icon for direction | Must | Visible and updates |
| FR-SORT-004 | Sorting independent per tab/table | Must | Low-battery sort doesn’t affect unavailable |
| FR-SORT-005 | Stable tie-breaker: Friendly Name | Must | Predictable ordering |
| FR-SORT-006 | Default sorts: Low-battery by Battery Level asc; Unavailable by Friendly Name asc | Must | Default ordering matches |

### 4.6 Infinite scroll / incremental loading
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-SCROLL-001 | Each tab table is infinitely scrollable, loading additional rows as user scrolls | Must | More rows appear when nearing bottom |
| FR-SCROLL-002 | Incremental loading must not break sorting correctness | Must | Newly loaded rows are inserted consistent with current sort |
| FR-SCROLL-003 | UI shows a loading indicator while fetching additional rows | Should | Visible feedback |

### 4.7 Low-battery threshold configuration
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-THR-001 | Default low-battery threshold is **15%** | Must | Fresh install uses 15% |
| FR-THR-002 | Threshold range is **5–100** with steps of **5%** | Must | Allowed values: 5,10,15,...,100 |
| FR-THR-003 | Threshold input is a **slider** | Must | Invalid input impossible |
| FR-THR-004 | Configurable during setup and editable later | Must | Config + options flow support |
| FR-THR-005 | Changing threshold updates UI without manual refresh | Must | Rows update |

### 4.8 Data sourcing: Home Assistant websocket
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-WS-001 | Frontend reads all data via HA websocket | Must | No polling |
| FR-WS-002 | Backend subscribes to HA websocket events to track entity state lifecycle (new/update/remove) | Must | Handles churn |
| FR-WS-003 | Backend maintains internal state and pushes row updates to frontend | Must | Fine-grained updates |
| FR-WS-004 | Frontend supports initial snapshot + incremental updates | Must | Correct after late connect |

## 5. Non-Functional Requirements

### 5.1 Performance
| ID | Requirement |
|---|---|
| NFR-PERF-001 | UI updates propagate within ≤ 2 seconds typical LAN |
| NFR-PERF-002 | Infinite scroll supports large lists (thousands of entities) without browser lockups |

### 5.2 Reliability & Resilience
| ID | Requirement |
|---|---|
| NFR-REL-001 | Event storms do not break correctness |
| NFR-REL-002 | Websocket reconnects resync state |

### 5.3 Security & Safety
| ID | Requirement |
|---|---|
| NFR-SEC-001 | Use HA auth/session model |
| NFR-SEC-002 | Delete action must be protected by confirmation and rely on HA permissions | 

## 6. Data Model (Conceptual)

### 6.1 EntityRecord
- `entity_id`
- `friendly_name`
- `state`
- `domain`
- `device_class`
- `unit_of_measurement`
- `battery_percent` (int|null)
- `battery_text` (low/medium/high|null)
- `manufacturer` (nullable)
- `model` (nullable)
- `area` (nullable)

### 6.2 Derived sets
- `low_battery_entities`:
  - numeric: `device_class=battery` and `unit == '%'` and `battery_percent <= threshold`
  - textual: `device_class=battery` and `battery_text == 'low'`
- `unavailable_entities`: `state == 'unavailable'`

## 7. Interface / API Overview

### 7.1 Frontend ↔ Backend websocket messages
- `snapshot`: `{ threshold_percent, tabs: { low_battery: {...}, unavailable: {...} } }`
- `entity_upsert`: `{ entity_id, row, table: 'low_battery'|'unavailable'|'none' }`
- `entity_remove`: `{ entity_id }`
- `threshold_update`: `{ threshold_percent }`

### 7.2 Delete entity action
Delete button must invoke the appropriate Home Assistant mechanism to remove the entity from the entity registry.

(Exact call/command is implementation detail; must be validated in architecture/engineering.)

## 8. Deployment & Release

- Target: HACS (publishing setup after UAT)
- Development: publish to Dek’s HA server for acceptance testing

## 9. Out of Scope
- Alerts/notifications

## 10. Key Decisions
- Entity-first approach for both tables.
- Threshold: default 15%, configurable, slider 5–100 step 5.
- Accept numeric battery only when unit is `%`.
- Textual battery vocab: `low/medium/high` only.
- Unavailable includes all entities with state `unavailable`.
- Unavailable rows include a delete-from-registry action with confirmation.
- Page UI uses two tabs; each tab supports infinite scroll.
- Default sorts: low-battery by battery asc; unavailable by name asc.
- Low-battery severity uses both color and an icon.

## 11. Open Questions (continuing)
| # | Question | Owner | Status |
|---:|---|---|---|
| 1 | Delete semantics: should delete remove only the entity registry entry, or also attempt to remove the underlying integration/device? | Product Owner | Open |
| 2 | Delete confirmation: single “Are you sure?” dialog, or require typing the entity_id? | Product Owner | Open |
| 3 | Infinite scroll page size: how many rows per fetch (e.g., 50/100/200)? | Product Owner | Open |
| 4 | When sorting is active, should infinite-scroll fetch be based on the sorted order (server-side) or fetch unsorted then sort client-side? | Product Owner | Open |
| 5 | Should we show counts on tabs (e.g., “Low Battery (7)”, “Unavailable (12)”) and update counts live? | Product Owner | Open |
| 6 | For textual low/medium/high: what should display in Battery Level column (raw text, or map to pseudo-%)? | Product Owner | Open |

## 12. Glossary
| Term | Definition |
|---|---|
| HA | Home Assistant |
| HACS | Home Assistant Community Store |
| Entity | Home Assistant entity |
| Unavailable | HA state indicating an entity is not available |
