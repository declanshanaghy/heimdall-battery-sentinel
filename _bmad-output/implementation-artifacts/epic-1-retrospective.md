# Epic 1 Retrospective

**Epic:** Core Integration Setup | **Stories:** 2 | **Date:** 2026-02-21

## What Went Well ✅

- Both stories completed with all acceptance criteria met
- Strong test coverage (26 tests passing across both stories)
- QA and UX reviews correctly identified backend-only stories as NOT_REQUIRED, avoiding unnecessary testing overhead
- Story 1-1 passed all reviewers on first pass with no rework needed

## Technical Patterns Established

- **HA Custom Integration Pattern**: Full integration structure with manifest.json, config_flow, options_flow, following Home Assistant conventions
- **Event-Driven Architecture**: Listeners for `state_changed` and registry updates (entity_registry_updated, device_registry_updated, area_registry_updated)
- **WebSocket Real-Time API**: Push notifications via `_notify_websocket()` connected to store updates
- **In-Memory Store with Subscriptions**: Store pattern with subscriber mechanism for notifying consumers of data changes

## Critical Risks

- **HIGH-1 Rework in Story 1-2**: Redundant notification path (both `store.notify_subscribers()` AND `_notify_websocket()`) caused duplicate WebSocket messages, requiring a CHANGES_REQUESTED iteration before acceptance
- **Documentation Drift**: File List in story 1-2 didn't match git reality (websocket.py and test file were from prior commits)
- **Dead Code in Tests**: TestStoreNotifications tests verify `store.notify_subscribers()` which is no longer called in production after the rework fix