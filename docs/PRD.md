# Product Requirements Document (PRD): Heimdall Battery Sentinel (Home Assistant)

**Version:** 1.5  
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
| 1.4 | 2026-02-19 | BA Agent | Added delete-entity action idea; tabs + infinite scroll; locked threshold range; link to entity page; accept only % units; include all unavailable; severity icons |
| 1.5 | 2026-02-19 | BA Agent | Removed delete action (link-only); server-side sorted infinite scroll (page=100) with loading/end indicators; tab live counts; textual battery shows only `low` |

## 1. Introduction

### 1.1 Purpose
Define the MVP product requirements for **Heimdall Battery Sentinel**, a Home Assistant (HA) integration that provides a dedicated sidebar page to surface:
- **Low battery entities** (entities with `device_class=battery`)
- **Unavailable entities** (any domain / any device_class)

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
- Unavailable tab includes all unavailable entities; rows link to entity page (no delete action)
- Robust handling of entity lifecycle (new, updated, removed) and edge cases

**Out of scope (MVP):**
- Notifications/alerts
- Search/filter box
- HACS publishing automation (until after UAT)

## 2. Product Overview

### 2.1 Product Vision
A fast, accurate, near-real-time “battery + availability health” view in HA that’s resilient to entity churn.

### 2.2 Target Users
Home Assistant power users managing many battery-powered sensors/devices.

## 3. Functional Requirements

### 3.1 Navigation, tabs, theme
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-UI-001 | Provide a **sidebar entry** to open the page | Must | Entry appears after install/reload |
| FR-UI-002 | Sidebar icon uses an **MDI low-battery icon** | Must | Matches chosen MDI glyph |
| FR-UI-003 | Page uses **two tabs**: Low Battery, Unavailable | Must | Tabs render; switching works |
| FR-UI-004 | Tabs show **live counts**: `Low Battery (N)`, `Unavailable (M)` | Must | Counts update as data changes |
| FR-UI-005 | Use HA theme (default / user preferred) | Must | Respects theme variables (works in dark mode) |

### 3.2 Low Battery tab (entity-based)
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-LB-001 | List entities with `device_class=battery` that are considered “low” | Must | Correct membership |
| FR-LB-002 | Columns: **Friendly Name**, **Manufacturer & Model**, **Area**, **Battery Level** | Must | Exact headers present |
| FR-LB-003 | Friendly Name links to the **entity page** | Must | Opens correct entity page |
| FR-LB-004 | Numeric batteries: only accept numeric state when unit is exactly `%` | Must | Non-% numeric ignored for thresholding |
| FR-LB-005 | Numeric Battery Level display: rounded integer with `%` | Must | `14.7` → `15%` |
| FR-LB-006 | Battery selection: assume no device has >1 numeric % battery entity; pick the first found | Must | Deterministic |
| FR-LB-007 | Textual batteries: support only `low/medium/high`; include only those currently `low` | Must | Only `low` appears |
| FR-LB-008 | Textual Battery Level display: show `low` | Must | Battery Level cell shows `low` |

### 3.3 Low-battery severity indicators
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-SEV-001 | Rows are color-coded by severity relative to threshold | Must | Color matches rule |
| FR-SEV-002 | Add a severity icon (MDI) indicating severity | Must | Icon changes with severity |

Severity rule (numeric batteries only):
- Threshold `T` default 15
- Battery `B`
- Include when `B <= T`
- ratio = (B / T) * 100:
  - 0–33 → red + most severe icon
  - 34–66 → orange + medium icon
  - 67–100 → yellow + least severe icon

### 3.4 Unavailable tab (entity-based)
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-UNAV-001 | List **all entities** whose state is exactly `unavailable` | Must | Accurate membership |
| FR-UNAV-002 | Columns: **Friendly Name**, **Manufacturer & Model**, **Area** | Must | Exact headers present |
| FR-UNAV-003 | Friendly Name links to the **entity page** | Must | Opens correct entity page |

### 3.5 Sorting
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-SORT-001 | All headers are clickable to sort by that column | Must | Click sorts |
| FR-SORT-002 | Repeated clicks toggle asc/desc | Must | Deterministic |
| FR-SORT-003 | Sorted header shows direction icon | Must | Visible and updates |
| FR-SORT-004 | Stable tie-breaker: Friendly Name | Must | Predictable ordering |
| FR-SORT-005 | Default sorts: Low-battery by Battery Level asc; Unavailable by Friendly Name asc | Must | Default ordering matches |
| FR-SORT-006 | Sorting is performed **server-side** | Must | Scroll loads next page in sorted order |

### 3.6 Infinite scroll / incremental loading
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-SCROLL-001 | Each tab is infinitely scrollable, loading more rows on scroll | Must | Additional rows load |
| FR-SCROLL-002 | Page size for load-more is **100 rows** | Must | Fetches in 100-row increments |
| FR-SCROLL-003 | Show a **Loading…** indicator while fetching more rows | Must | Visible during fetch |
| FR-SCROLL-004 | Show an **End of list** indicator when no more rows are available | Must | Visible at end |

### 3.7 Threshold configuration
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-THR-001 | Default threshold is **15%** | Must | Fresh install uses 15 |
| FR-THR-002 | Threshold slider range **5–100**, step **5** | Must | Allowed: 5,10,15,…,100 |
| FR-THR-003 | Threshold configurable during setup and editable later | Must | Config + options flow |
| FR-THR-004 | Changing threshold updates UI (membership + severity) without refresh | Must | Live updates |

### 3.8 Data sourcing / update flow
| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---:|---|
| FR-WS-001 | Frontend reads data via HA websocket | Must | No polling |
| FR-WS-002 | Backend subscribes to HA events for entity lifecycle (new/update/remove) | Must | Handles churn |
| FR-WS-003 | Backend maintains internal state and pushes fine-grained updates | Must | Row-level updates |
| FR-WS-004 | Frontend supports initial snapshot + incremental updates | Must | Correct after late connect |

## 4. Deployment
- Target: HACS (publishing setup after UAT)
- Development/UAT: publish directly to Dek’s HA server

## 5. Key Decisions (summary)
- Entity-first approach for low-battery and unavailable.
- Threshold: default 15%, slider 5–100 step 5, editable anytime.
- Numeric batteries only if unit is `%`; textual only `low/medium/high` and show only `low`.
- Two tabs with live counts.
- Infinite scroll with page size 100 + loading/end indicators.
- Sorting is server-side.
- Low battery severity uses color + MDI icon.
