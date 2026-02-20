# Technical Architecture: heimdall-battery-sentinel

**Version:** 1.0  
**Date:** 2026-02-20  
**Author:** Architect Agent

## 1. Overview

### 1.1 System Context
Heimdall Battery Sentinel is a Home Assistant (HA) custom integration that adds a dedicated **sidebar page** showing two live, sortable, infinitely scrollable tables:

- **Low Battery**: entities with `device_class=battery` that are “low” based on a configurable threshold (numeric `%` only) or textual `low/medium/high` (include only `low`).
- **Unavailable**: **all entities** whose state is exactly `unavailable`.

The system is **event-driven**:
- Backend subscribes to HA state/entity lifecycle events and maintains an internal, derived view.
- Frontend uses **Home Assistant WebSocket** to fetch an initial snapshot and receive incremental updates (no polling).

### 1.2 Architecture Principles
1. **HA-native patterns first** — Use Home Assistant’s registries, config flows, and websocket patterns to reduce maintenance burden.
2. **Event-driven, no polling** — Meet the PRD requirement for websocket-driven UI and minimize HA load.
3. **Derived state is cached, source of truth remains HA** — HA state machine is authoritative; we cache computed lists for fast UI.
4. **Server-side pagination + sorting** — Required by PRD; keeps frontend light and avoids shipping huge tables.
5. **Deterministic behavior** — Stable tie-breakers, consistent entity selection rules, and predictable updates.
6. **Graceful degradation** — Missing device/area metadata should not break rendering; show best-effort values.

## 2. Technology Stack

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| Runtime | Python (Home Assistant Core) | HA-managed | HA custom integrations are Python; leverages HA event bus/state machine. |
| Backend API | Home Assistant `websocket_api` | HA-managed | PRD requires websocket-based frontend data access; integrates cleanly with HA auth/session. |
| Frontend | Home Assistant Custom Panel (JS/TS) using Lit + HA UI components | HA-managed | Matches HA frontend architecture and theming; avoids bespoke UI frameworks. |
| Packaging/Distribution | HACS custom repository format | N/A | Target distribution per PRD; standard for HA community installs. |
| Testing | `pytest` + HA test harness | HA-managed | Standard for HA integration tests; enables event-driven unit/integration tests. |
| CI (recommended) | GitHub Actions (lint/test) | N/A | Fast feedback; aligns with HACS expectations and community norms. |

## 3. Architecture Decisions

### ADR-001: Implement as a Home Assistant custom integration + custom sidebar panel

**Status:** Accepted  
**Date:** 2026-02-20

**Context:** The product must add a sidebar page in HA and integrate with HA’s entity model, registries, and authentication.

**Decision:** Build a custom integration under `custom_components/heimdall_battery_sentinel/` that registers a sidebar panel (custom panel) and provides websocket commands for data retrieval + subscriptions.

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Custom integration + custom panel | HA-native UX, uses HA auth, deployable via HACS, easy event access | Requires frontend build pipeline; panel conventions to follow |
| Standalone web app + HA long-lived token | Faster UI iteration | Breaks HA-native navigation/auth; violates websocket/no-polling intent; more operational complexity |
| Lovelace-only dashboard card | Simpler JS | Doesn’t meet “dedicated sidebar page” requirement cleanly; harder to implement server-side paging/sorting |

**Rationale:** Aligns with HA patterns and PRD requirements while minimizing operational complexity.

**Consequences:**
- Must maintain a small frontend build artifact (JS module) served to HA.
- Need to manage compatibility with HA frontend API changes over time.

---

### ADR-002: Event-driven backend cache derived from HA state + registries

**Status:** Accepted  
**Date:** 2026-02-20

**Context:** UI requires live counts and updates without polling, and must handle entity churn (new/update/remove).

**Decision:** Maintain an in-memory cache of derived row models for both tables, updated via subscriptions to HA events (state changes + registry updates as needed). HA remains the source of truth.

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| In-memory derived cache (per HA runtime) | Fast, simple, resets on restart (acceptable), minimal dependencies | Needs careful invalidation on registry changes/reloads |
| Persisted DB (SQLite) | Survives restarts | Unnecessary; adds complexity, migrations, potential data drift |
| Compute everything on-demand for each websocket request | Simplest correctness | Potentially expensive for large installations; harder to provide fine-grained incremental updates |

**Rationale:** Best balance of performance and simplicity; HA restarts already reset runtime state.

**Consequences:**
- Cache must be recomputed on startup and when config/options change.
- Must manage consistency between state changes and metadata lookups.

---

### ADR-003: WebSocket API for snapshot, paging, sorting, and subscriptions

**Status:** Accepted  
**Date:** 2026-02-20

**Context:** PRD mandates frontend reads via websocket (no polling) and requires server-side sorting + paging (page size 100).

**Decision:** Implement websocket commands:
- `heimdall/summary` → counts, threshold, current sort state (optional).
- `heimdall/list` → paged list for a tab with `page_size=100`, `page_token|offset`, `sort_by`, `sort_dir`.
- `heimdall/subscribe` → push incremental updates (row upsert/remove + count changes + “dataset invalidated” signals).

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| HA websocket commands | Meets requirements; uses HA session/auth; supports push updates | Requires defining message formats + versioning |
| HTTP endpoints (`http` component) | Familiar REST semantics | Violates “frontend reads via websocket”; would need separate auth/CSRF patterns |
| Frontend reads HA state directly | Minimal backend API | Hard to do server-side sorting/paging and derived rules reliably; harder to keep stable behavior |

**Rationale:** Websocket is the correct HA-native transport for real-time UI.

**Consequences:**
- Must document message schemas and maintain backward compatibility (or version messages).

---

### ADR-004: Server-side sorting with stable tie-breaker = Friendly Name

**Status:** Accepted  
**Date:** 2026-02-20

**Context:** PRD requires server-side sorting and stable deterministic ordering.

**Decision:** Sort on the backend for every query and for incremental update application. Use a stable tie-breaker: `friendly_name` (casefolded), then `entity_id` as a final deterministic tie-break.

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Backend sorting (required) | Consistent paging; meets PRD | Must keep sorting logic in sync with frontend column keys |
| Frontend sorting | Simple UI | Violates PRD; breaks paging correctness |

**Rationale:** Required and improves scalability.

**Consequences:**
- Changes to sort keys must be coordinated across backend + UI.

---

### ADR-005: Battery evaluation rules exactly match PRD (numeric % only; textual low only)

**Status:** Accepted  
**Date:** 2026-02-20

**Context:** The definition of “low battery” is strict: numeric is only valid if unit is exactly `%`, and textual only includes `low`.

**Decision:** Implement rule engine:
- Numeric: accept only if `state` parses as number AND `unit_of_measurement == "%"`.
- Include in Low Battery if `B <= threshold`.
- Display numeric as `round(B)` with `%`.
- Textual: only accept string states in `{low, medium, high}` (case-insensitive); include only if `low`; display `low`.
- Battery selection per device: assume <=1 numeric % battery entity per device; if multiple candidates exist, choose first by deterministic ordering (entity_id ascending).

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Strict PRD rules | Predictable, matches acceptance criteria | Excludes some real-world devices (e.g., unitless %, alternative units) |
| Lenient parsing/heuristics | Broader device compatibility | Violates PRD; can misclassify batteries |

**Rationale:** MVP must match explicit acceptance criteria.

**Consequences:**
- Some user devices may not show up until they expose `%` correctly.
- Could add optional heuristics later (post-MVP) behind a setting.

---

### ADR-006: Metadata enrichment uses HA registries (device + area) with best-effort fallbacks

**Status:** Accepted  
**Date:** 2026-02-20

**Context:** Tables require Manufacturer/Model and Area. These are not reliably in entity state attributes.

**Decision:** Resolve metadata via:
- `entity_registry` → device_id, entity naming
- `device_registry` → manufacturer, model
- `area_registry` → area name via device’s area or entity’s area (prefer device area, fallback entity area)
Cache resolved metadata per `entity_id` / `device_id` and invalidate on registry update events.

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Use registries | Correct, HA-native, stable | Must handle missing links and invalidation |
| Only use state attributes | Simpler | Often incomplete/inconsistent; fails acceptance criteria |

**Rationale:** Registries are the authoritative place for device/area metadata.

**Consequences:**
- Need robust null handling (e.g., unknown area/manufacturer).

---

### ADR-007: Threshold configuration via config flow + options flow

**Status:** Accepted  
**Date:** 2026-02-20

**Context:** Threshold must be configurable at setup and editable later (range 5–100, step 5), and changing it must update UI live.

**Decision:** Provide:
- `config_flow.py` for initial setup (default 15).
- `options_flow.py` to edit threshold later.
- Store threshold in config entry options.
- On options update: recompute derived low-battery dataset and push websocket “dataset invalidated” + new summary counts.

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Config + options flow | Standard UX; matches requirement | More code than simple YAML |
| YAML-only config | Simple for developers | Non-standard for many users; not editable in UI |

**Rationale:** HA UX expectations + PRD requirement.

**Consequences:**
- Need migration handling if options schema evolves.

---

### ADR-008: Paging model uses offset-based pagination with “dataset version” invalidation

**Status:** Accepted  
**Date:** 2026-02-20

**Context:** Infinite scroll must work while entities are changing in real time. Pure offset paging can drift.

**Decision:** Use a dataset versioning approach:
- Backend maintains `dataset_version` for each tab that increments on structural changes (membership changes, resort-required changes, threshold change).
- `heimdall/list` requests include the client’s `dataset_version`; if stale, backend responds with an `invalidated=true` flag prompting the client to refresh from page 0.
- For minor row updates that don’t affect ordering/membership (e.g., manufacturer text fix), send row upserts on the subscription channel.

**Options Considered:**

| Option | Pros | Cons |
|--------|------|------|
| Offset paging + version invalidation | Simple; robust to churn; easy to implement | Occasional refresh UX when churn is high |
| Cursor-based paging | More stable under changes | Complex sort-key cursor design; harder with multi-column sorts |

**Rationale:** Good trade-off for MVP, avoids complex cursor semantics.

**Consequences:**
- UI must handle invalidation signals gracefully.

## 4. System Architecture

### 4.1 High-Level Diagram

```
┌───────────────────────────┐
│ Home Assistant Frontend    │
│  - Sidebar Panel UI        │
│  - Tabs + tables           │
│  - Infinite scroll         │
└───────────────┬───────────┘
                │ WebSocket (HA session)
                ▼
┌───────────────────────────┐
│ Heimdall Battery Sentinel  │
│ (custom integration)       │
│  - Event subscriptions     │
│  - Derived cache           │
│  - WS commands             │
└───────────────┬───────────┘
                │
                ▼
┌───────────────────────────┐
│ Home Assistant Core        │
│  - State machine           │
│  - Entity/Device/Area regs │
│  - Event bus               │
└───────────────────────────┘
```

### 4.2 Components

**Backend (Python / custom integration)**
- `__init__.py`: integration setup/teardown, subscribe to events, init caches.
- `const.py`: domain constants, websocket command names, defaults.
- `config_flow.py` + `options_flow.py`: threshold configuration.
- `models.py`: typed row models (low battery row, unavailable row) + sort keys.
- `evaluator.py`: battery evaluation rules (numeric/textual), severity calculation.
- `registry.py`: metadata enrichment helpers and caching.
- `store.py`: in-memory datasets + dataset_version + subscriber management.
- `websocket.py`: websocket command registration + message schema validation.

**Frontend (Custom panel module)**
- Panel registration (shows in sidebar with MDI low-battery icon).
- UI view:
  - Tabs: `Low Battery (N)` and `Unavailable (M)`.
  - Sortable table headers with direction icon.
  - Infinite scroll list with page size 100.
  - Loading and end-of-list indicators.
  - Row rendering with severity icon + theme-aware color.
  - Friendly name links to HA entity page.
- Websocket client:
  - On load: request summary + first page for active tab.
  - Subscribe to updates; apply upsert/remove; react to invalidation.

## 5. Data Architecture

### 5.1 Database Schema
No external database. Data is derived from HA in-memory state and registries.

Define internal, in-memory models (conceptual schema):

**LowBatteryRow**
- `entity_id: str`
- `friendly_name: str`
- `manufacturer: str | None`
- `model: str | None`
- `area: str | None`
- `battery_display: str` (e.g., `"15%"` or `"low"`)
- `battery_numeric: float | None` (for sorting when numeric)
- `severity: enum{yellow, orange, red} | None` (numeric only)
- `updated_at: datetime`

**UnavailableRow**
- `entity_id: str`
- `friendly_name: str`
- `manufacturer: str | None`
- `model: str | None`
- `area: str | None`
- `updated_at: datetime`

**Dataset State**
- `threshold: int` (5..100 step 5)
- `low_battery_version: int`
- `unavailable_version: int`
- `low_battery_rows_by_id: dict[str, LowBatteryRow]`
- `unavailable_rows_by_id: dict[str, UnavailableRow]`

### 5.2 Relationships
- `entity_id` → entity registry entry (may reference `device_id`).
- `device_id` → device registry entry (manufacturer/model, area_id).
- `area_id` → area registry entry (name).

### 5.3 Row-Level Security
Not applicable. HA websocket access is already authenticated/authorized by HA. The panel runs within HA’s UI session.

## 6. API Design

### 6.1 Style
Home Assistant websocket commands (JSON messages). Version schemas explicitly to allow evolution.

Recommended command set (initial):
- `heimdall/summary`
- `heimdall/list`
- `heimdall/subscribe`

### 6.2 Authentication
Inherits HA authentication:
- Frontend websocket is opened by HA UI with the user’s session.
- Backend websocket commands run under HA’s websocket API authorization.

Recommended authorization rules:
- Require authenticated user.
- Optionally require admin for configuration actions (threshold editing is handled via options flow UI, not websocket).

### 6.3 Error Handling
Use HA websocket error patterns:
- Validate payloads; return `result: false` with `error` object (code + message).
- Never raise raw exceptions to the websocket; log server-side with rate limiting.

Example error envelope (conceptual):
```json
{
  "id": 12,
  "type": "result",
  "success": false,
  "error": {
    "code": "invalid_format",
    "message": "sort_by must be one of: friendly_name, area, battery_level"
  }
}
```

### 6.4 Data Contracts (conceptual)
**List request**
- `tab`: `low_battery | unavailable`
- `sort_by`: column key
- `sort_dir`: `asc | desc`
- `offset`: int (0,100,200...)
- `page_size`: fixed 100
- `dataset_version`: int

**List response**
- `rows: [...]`
- `next_offset: int | null`
- `end: bool`
- `dataset_version: int`
- `invalidated: bool`

**Subscribe events**
- `type: upsert | remove | summary | invalidated`
- `tab`
- `row` or `entity_id`
- `counts` for summary
- `dataset_version`

## 7. Project Structure

Recommended repository layout:

```
custom_components/heimdall_battery_sentinel/
├── __init__.py
├── const.py
├── config_flow.py
├── options_flow.py
├── evaluator.py
├── models.py
├── registry.py
├── store.py
├── websocket.py
└── manifest.json
frontend/
├── src/
│   ├── panel-heimdall.ts
│   ├── components/
│   ├── api/
│   └── styles/
└── dist/
    └── panel-heimdall.js
hacs.json
README.md
docs/
├── PRD.md
└── architecture.md
```

Notes:
- `frontend/dist` is what HA serves; `frontend/src` is authored code.
- Keep message schemas in `websocket.py` close to backend store logic.

## 8. Coding Standards

### 8.1 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python modules | snake_case | `config_flow.py` |
| HA domain | lowercase | `heimdall_battery_sentinel` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_THRESHOLD` |
| Frontend components | kebab-case custom elements | `<heimdall-panel>` |
| TS classes/types | PascalCase | `LowBatteryRow` |

### 8.2 Error Handling
- Backend:
  - Validate all websocket payloads.
  - Catch and log exceptions at command handler boundaries.
  - Prefer explicit `HomeAssistantError` for known failures.
- Frontend:
  - Show non-blocking error banners/toasts on transient failures.
  - Retry subscription connection with backoff if websocket channel drops.

### 8.3 Logging
- Use HA logger per module (`_LOGGER = logging.getLogger(__name__)`).
- Avoid noisy logs on high-frequency state changes; add throttling if needed.

### 8.4 Type Safety
- Backend: add type hints for models and evaluator logic.
- Frontend: TypeScript types for websocket payloads and rows.

## 9. Testing Strategy

| Type | Tool | Target |
|------|------|--------|
| Unit | `pytest` | Battery evaluator rules; severity thresholds; sorting keys |
| Integration | HA test harness | Event subscription updates; dataset version invalidation; websocket commands |
| Frontend | `web-test-runner` or `vitest` (optional) | Sorting toggle logic; infinite scroll state machine |
| E2E (optional) | Playwright (optional) | Render panel, scroll loads, live updates (harder in HA context) |

Key test cases (must-have):
- Numeric battery accepted only with `%` unit; rounding rules.
- Threshold inclusion and severity buckets.
- Textual `low/medium/high` handling; only `low` included.
- Unavailable membership is state exactly `unavailable`.
- Server-side sorting correctness + tie-breaker stability.
- Pagination returns exactly 100 rows per page and end-of-list indicator.
- Dataset invalidation on churn or threshold change.

## 10. Security Considerations
- Rely on HA websocket auth; do not introduce additional tokens.
- Validate all websocket input (sort keys, offsets) to avoid crashes.
- Avoid exposing unnecessary internal state; return only required row fields.
- Rate-limit expensive operations and protect against accidental high-frequency UI calls.

## 11. Performance Considerations
- Maintain O(1) updates where possible by indexing rows by `entity_id`.
- Only recompute full datasets on:
  - startup
  - threshold change
  - bulk registry reload (or explicit invalidation)
- For high-churn environments:
  - batch websocket push updates (coalesce within a short debounce window).
- Keep metadata lookups cached; registry reads can be non-trivial at scale.

## 12. Deployment
- Dev/UAT: install as a custom repository on the target HA server (per PRD).
- Target distribution: HACS.

Recommended release steps:
1. Ensure `manifest.json`, `hacs.json`, and versioning follow HACS guidelines.
2. Provide a minimal README with install instructions.
3. Add CI for linting and tests.
4. Tag releases after UAT.
