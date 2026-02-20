# Product Requirements Document (PRD): Heimdall Battery Sentinel (Home Assistant)

**Version:** 1.3  
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
- Two tables: low battery entities, unavailable entities
- Configurable low-battery threshold (default 15%) editable at setup and later
- Column sorting on both tables with icons and asc/desc toggle
- Low-battery row color coding by severity
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
- Anyone wanting a quick “what needs attention” view without building custom dashboards

### 2.3 Success Metrics (MVP)
- **Correctness:** Table membership and row contents match HA entity state across updates, restarts, add/remove.
- **Latency:** UI row updates within **≤ 2 seconds** of entity state changes under normal HA load.
- **Completeness:** All entities with `device_class=battery` are considered for low-battery tracking.
- **Stability:** No runaway memory growth; cleanly handles event storms (many state changes).
- **Usability:** Sorting works consistently, indicates sort direction, and feels stable.

## 3. User Journeys

### UJ-1: View low battery entities
**Persona:** Home automation owner

1. User clicks **Heimdall Battery Sentinel** in the HA sidebar (MDI low-battery icon).
2. User sees a table of **low battery entities** with:
   - friendly name (link)
   - manufacturer & model (if available)
   - area (if available)
   - battery level
3. User clicks the link to investigate in HA.

**Success criteria:**
- Low battery list is accurate.
- Sorting is available on all columns.
- Rows are color-coded by severity.

### UJ-2: View unavailable entities
1. User opens the same sidebar page.
2. User sees a second table listing **unavailable entities** (any domain).
3. User clicks the entity link to troubleshoot.

**Success criteria:**
- Unavailable list is accurate and updates automatically when entity state changes.
- Default sort is by name ascending.

### UJ-3: Change threshold and see the page update
1. User edits the integration’s **low battery threshold** (default 15%) after setup.
2. Integration applies the new threshold.
3. The page updates (rows move in/out of low-battery table; severity colors may change) without requiring a manual refresh.

**Success criteria:**
- Threshold can be changed at any time.
- UI updates to reflect the new rule.

### UJ-4: Real-time updates while page is open
1. A tracked entity’s state changes (battery % changes, becomes `unavailable` / recovers).
2. Backend receives relevant HA websocket events.
3. Backend updates internal state.
4. Backend pushes an update over websocket to the frontend.
5. Frontend finds the matching row (or creates/removes it) and updates displayed values.

**Success criteria:**
- No full-page refresh required.
- Row is created/updated/removed in the correct table with correct data.

## 4. Functional Requirements

### 4.1 Navigation, look & feel
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-UI-001 | Integration provides a **sidebar entry** that opens the Battery Sentinel page | Must | Entry appears in sidebar after install/reload |
| FR-UI-002 | Sidebar icon uses an **MDI low-battery icon** | Must | Icon matches selected MDI low-battery glyph |
| FR-UI-003 | The page contains **two sections**: Low Battery, Unavailable | Must | Both sections render, even if empty |
| FR-UI-004 | Page uses the **Home Assistant default theme** / user’s preferred theme | Must | Styling respects HA theme variables; no hard-coded background/text that breaks dark mode |

### 4.2 Low Battery table (entity-based)
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-LB-001 | The page lists entities with `device_class=battery` whose battery level is considered “low” | Must | Entities meeting criteria appear; others do not |
| FR-LB-002 | Low battery table headers are: **Friendly Name**, **Manufacturer & Model**, **Area**, **Battery Level** | Must | Column headers and data present |
| FR-LB-003 | Friendly Name is a **link** to the relevant HA UI page for investigation | Must | Clicking opens the correct HA UI destination |
| FR-LB-004 | Battery Level is shown as a rounded integer percent with a `%` suffix for numeric batteries | Must | e.g., `14.7` → `15%` |
| FR-LB-005 | Battery selection: assume a device will not have >1 numeric battery entity; choose the **first numeric** battery entity found | Must | Correct numeric entity chosen |
| FR-LB-006 | Textual batteries: if an entity reports only `low/medium/high`, treat **`low`** as low-battery and include it | Must | `low` appears; `medium/high` do not |

### 4.3 Low-battery severity row coloring
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-COLOR-001 | Low-battery rows are color-coded by “how low” relative to the configured threshold | Must | Color changes as battery changes |
| FR-COLOR-002 | Color bands are based on percentage-of-threshold remaining: 0–33% → red; 34–66% → orange; 67–100% → yellow | Must | Example: threshold=15, battery=5 → red; battery=9 → orange; battery=14 → yellow |
| FR-COLOR-003 | Colors must look good under HA themes (light/dark) | Must | Uses theme variables or accessible contrast |

**Rule definition:**
- Let `T` = threshold percent (default 15)
- Let `B` = battery percent (0..100)
- If `B <= T`, entity is in low-battery table.
- Severity band uses `ratio = (B / T) * 100`:
  - `0..33` → red
  - `34..66` → orange
  - `67..100` → yellow

### 4.4 Unavailable table (entity-based)
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-UNAV-001 | The page lists entities whose state is exactly `unavailable` | Must | Unavailable entities appear; available entities do not |
| FR-UNAV-002 | Unavailable table headers are: **Friendly Name**, **Manufacturer & Model**, **Area** | Must | Column headers and data present |
| FR-UNAV-003 | Friendly Name is a **link** to the relevant HA UI page for investigation | Must | Clicking opens correct destination |

### 4.5 Sorting
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-SORT-001 | All table headers are clickable to sort by that column | Must | Clicking a header sorts rows by that column |
| FR-SORT-002 | Repeated clicks on the same header alternate between ascending and descending | Must | Sort toggles asc/desc deterministically |
| FR-SORT-003 | Show an icon in the sorted column header indicating current sort direction | Must | Icon is visible and updates when direction changes |
| FR-SORT-004 | Sorting applies independently to each table | Must | Sorting low-battery doesn’t affect unavailable (and vice versa) |
| FR-SORT-005 | Sorting is stable: ties use secondary sort by Friendly Name | Must | When values tie, ordering is predictable |
| FR-SORT-006 | Default sort on load: Low-battery sorts by Battery Level asc; Unavailable sorts by Friendly Name asc | Must | Default ordering matches |

### 4.6 Low-battery threshold configuration
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-THR-001 | Default low-battery threshold is **15%** | Must | Fresh install uses 15% |
| FR-THR-002 | Threshold range is **1–100** with steps of **5%** | Must | Values are {1,6,11,...}? (see Open Questions to confirm exact step behavior) |
| FR-THR-003 | Threshold input is a **slider** so invalid input cannot be given | Must | No free-form text field |
| FR-THR-004 | During integration setup, user can configure the threshold | Must | Config flow includes slider |
| FR-THR-005 | User can edit the threshold at any time after setup | Must | Options flow updates stored value |
| FR-THR-006 | Changing threshold updates UI list membership without manual refresh | Must | Rows move in/out appropriately |

### 4.7 Data sourcing: Home Assistant websocket
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-WS-001 | Frontend page reads all data from Home Assistant via the **Home Assistant websocket service** | Must | No REST polling required for normal operation |
| FR-WS-002 | Backend subscribes to relevant HA events to receive entity updates | Must | Updates arrive for state changes, new entities, removed entities |
| FR-WS-003 | On receiving an update, backend updates internal state and emits an update message to the frontend over websocket | Must | Frontend updates specific row without full reload |
| FR-WS-004 | Events can include **new entities** and **removed entities**; system handles both gracefully | Must | New entities appear when they meet criteria; removed entities disappear |

### 4.8 Edge cases & correctness
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-EDGE-001 | If an entity moves between categories (battery recovers, becomes unavailable, etc.), row moves to/from the correct table | Must | Row appears in correct table(s) per defined logic |
| FR-EDGE-002 | If required metadata is missing (manufacturer/model/area), UI shows a safe placeholder (e.g., “—”) | Must | No crashes; row renders |
| FR-EDGE-003 | On HA restart / integration reload, internal state is rebuilt and UI shows correct current state | Must | After restart, tables reflect reality |
| FR-EDGE-004 | If frontend connects late, it receives a full initial snapshot plus incremental updates afterward | Must | UI is correct even if page opened later |

## 5. Non-Functional Requirements

### 5.1 Performance
| ID | Requirement |
|---|---|
| NFR-PERF-001 | UI updates propagate within **≤ 2 seconds** from HA change to visible row update (typical LAN HA installs) |
| NFR-PERF-002 | Integration must handle at least **2000 entities** without excessive CPU usage or UI lag |

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
Entity-first approach.

#### EntityRecord
- `entity_id` (string)
- `friendly_name` (string)
- `state` (string)
- `domain` (string)
- `device_class` (string|null)
- `battery_percent` (int|null) — rounded integer percent when numeric
- `battery_text` (string|null) — e.g., `low/medium/high`
- `manufacturer` (string|null)
- `model` (string|null)
- `area` (string|null)
- `last_updated` (timestamp)

### 6.2 Derived sets
- `low_battery_entities`:
  - numeric case: `device_class=battery` and `battery_percent <= threshold`
  - textual case: `device_class=battery` and `battery_text == 'low'`
- `unavailable_entities`: `state == 'unavailable'`

## 7. Interface / API Overview

### 7.1 Frontend ↔ Backend messaging (websocket)
The frontend expects:
- An **initial snapshot** message containing the full computed tables
- **Incremental update** messages keyed by `entity_id` to update/move/remove a row

Suggested message types:
- `snapshot`: `{ threshold_percent, sort_state, low_battery: EntityRow[], unavailable: EntityRow[] }`
- `entity_upsert`: `{ entity_id, row, table: 'low_battery'|'unavailable'|'none' }`
- `entity_remove`: `{ entity_id }`
- `threshold_update`: `{ threshold_percent }`

### 7.2 Links to HA UI
Friendly-name links must open the correct HA UI destination.

(Exact routes vary; validate during UAT.)

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
- Low-battery and unavailable views are **entity-based**, not device-based.
- Low-battery tracks entities with `device_class=battery`.
- Default low-battery threshold is **15%**, configurable during setup and after setup via slider.
- Threshold slider step is **5%**.
- Numeric battery values are rounded and always displayed with `%`.
- Textual battery vocab supported in MVP: `low/medium/high` only; `low` counts as low-battery.
- Unavailable table includes **any entity** with state exactly `unavailable`.
- Primary UI is a sidebar-linked page with an MDI low-battery icon.
- UI shows two tables: low batteries and unavailable.
- All table headers are clickable for sorting with asc/desc toggle, direction icon, and stable tie-break on Friendly Name.
- Default sorts: low-battery by battery asc; unavailable by name asc.
- Low-battery rows are color-coded based on percentage-of-threshold.
- Frontend reads via Home Assistant websocket; backend subscribes to HA events, maintains internal state, and pushes updates to frontend.
- Target distribution is HACS, but publishing setup is delayed until after UAT.

## 11. Assumptions
- HA websocket APIs provide sufficient event data to maintain accurate state.
- Manufacturer/model/area are derivable for many entities (but not all).

## 12. Open Questions (continuing)
| # | Question | Owner | Status |
|---:|---|---|---|
| 1 | Threshold slider stepping: do you want values **exactly multiples of 5** (5,10,15,...) or allow 1 as min but still step by 5 (1,6,11,...)? | Product Owner | Open |
| 2 | For low-battery table links: should the link open the **Entity detail page** (preferred now that we’re entity-based), or still open the **Device page** when available? | Product Owner | Open |
| 3 | What should we do for `device_class=battery` entities with numeric state but **unit not %** (e.g., volts), if they exist? Ignore, or treat numeric as percent anyway? | Product Owner | Open |
| 4 | Unavailable table membership: include **all** unavailable entities, or only entities that have a device_id / area / manufacturer? (PO said “just deal with entities”, but confirm whether we include entities even if metadata is empty.) | Product Owner | Open |
| 5 | UX: should we add a **table search/filter box** (client-side) in MVP, or rely on sorting only? | Product Owner | Open |
| 6 | Severity coloring + accessibility: should we also add a **text badge** (e.g., “CRITICAL/WARN”) for colorblind accessibility, or is color-only fine for MVP? | Product Owner | Open |
| 7 | Should the tables paginate, or just render all rows? If pagination, what page size? | Product Owner | Open |

## 13. Glossary
| Term | Definition |
|---|---|
| HA | Home Assistant |
| HACS | Home Assistant Community Store |
| Entity | Home Assistant entity (sensor, binary_sensor, etc.) |
| device_class=battery | Entity classification indicating battery status/level |
| Unavailable | HA state indicating an entity is not currently available |
