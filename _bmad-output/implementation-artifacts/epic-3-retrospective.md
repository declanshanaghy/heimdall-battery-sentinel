# Epic 3 Retrospective

**Epic:** Unavailable Tracking | **Stories:** 2 | **Date:** 2026-02-21

## What Went Well ✅

- **Event-driven architecture proved solid**: ADR-002 pattern (synchronous cache invalidation) worked well across both stories; sub-millisecond latency achieved (<0.1ms vs 5-second requirement)
- **Prior epic learnings applied proactively**: Epic 2 recommendations on AC4-type invariant testing were followed; both batch AND incremental paths tested
- **Test coverage comprehensive**: 177 tests passing with no regressions; new tests added for metadata resolution and cache invalidation

## Technical Patterns Established

- **MetadataResolver pattern**: Centralized registry lookup in registry.py per ADR-006; handles manufacturer/model/area resolution with caching
- **Dataset versioning**: Every mutation (upsert/remove/bulk_set) increments version for frontend cache invalidation; applies uniformly across all datasets
- **Registry event subscription**: Event listeners for device/area/entity registry updates with cache invalidation; enables real-time metadata refresh

## Critical Risks

- **Incremental path overlooked in initial implementation**: Versioning only in bulk_set methods, not incremental upsert/remove; required rework to fix
- **Frontend-backend handoff requires coordination**: Backend serializes metadata ("Unknown"/"Unassigned"), frontend renders; story 3-2 completion depended on frontend (story 4-*) task checklist being accurate
