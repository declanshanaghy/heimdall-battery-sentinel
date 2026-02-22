# Story 4.5: Deployment

Status: in-progress
<!-- NOTE: Status values MUST match sprint-status.yaml exactly: backlog | ready-for-dev | in-progress | review | done -->

## Story

As a Home Assistant user,
I want the integration to be published to HACS with proper versioning,
so that I can easily install and update it through the Home Assistant Community Store.

## Acceptance Criteria

1. Given the integration is complete, when deploying to production, then it should be published to HACS (Home Assistant Community Store)
2. Given the release is created, when users view the release, then it should include proper versioning using semver (e.g., v1.0.0)
3. Given the release is created, when users view the release, then it should have a proper release workflow with changelog

## Tasks / Subtasks

- [x] Create HACS configuration files (AC: #1)
  - [x] Create `hacs.json` with required HACS metadata
  - [x] Create `info.md` with integration description
  - [x] Verify manifest.json meets HACS requirements
- [x] Set up GitHub release workflow (AC: #2, #3)
  - [x] Create `.github/workflows/release.yml`
  - [x] Configure semver tagging
  - [x] Configure automatic changelog generation
- [ ] Verify all stories are complete before deployment (AC: #1)
  - [ ] Confirm all Epic 4 stories are done
  - [x] Run full test suite
- [ ] Create initial release (AC: #1, #2, #3)
  - [ ] Tag first release v1.0.0
  - [ ] Create GitHub release with changelog
  - [ ] Submit to HACS (if required)

## Dev Notes

### Architecture Requirements
- Must follow HACS custom repository format ([Source: planning-artifacts/architecture.md#1.1])
- Release workflow should use GitHub Actions ([Source: planning-artifacts/architecture.md#12])
- All acceptance criteria must be met before publishing

### Technical Specifications
- Use semantic versioning (semver) for releases
- HACS requires: hacs.json, manifest.json, proper domain naming
- Release workflow should auto-generate changelog from conventional commits

### File Structure
1. `hacs.json` - HACS metadata file (create)
2. `info.md` - Integration information (create)
3. `.github/workflows/release.yml` - Release workflow (create)
4. `manifest.json` - Update if needed for HACS compliance
5. `README.md` - Update with HACS installation instructions

### Testing Requirements
- Verify all tests pass before release
- Test HACS installation locally (if possible)
- Verify release workflow works on a test tag

### References
- [Source: planning-artifacts/epics.md#4.5-Deployment]
- [Source: planning-artifacts/architecture.md#12-Deployment]
- [Source: planning-artifacts/prd.md#4-Deployment]

## Dev Agent Record

### Agent Model Used
openrouter/minimax/minimax-m2.5

### Debug Log References
N/A - No issues encountered during implementation

### Completion Notes List
- Created hacs.json with HACS-compliant metadata (name, description, country, homeassistant min version)
- Created info.md with comprehensive integration documentation including installation instructions
- Verified manifest.json meets HACS requirements (domain, name, version, documentation, codeowners, dependencies)
- Created .github/workflows/release.yml with modern GitHub Actions (softprops/action-gh-release)
- Configured semver tagging via tag pattern matching (v*)
- Configured automatic changelog generation from git commits
- Ran full test suite: 101 tests passed
- Created README.md with HACS installation instructions
- Note: Epic 4 stories 4-1 through 4-4 not yet complete - deployment release should happen after Epic 4 is fully done
- Note: manifest.json version currently 0.0.1 - should be updated to 1.0.0 before tagging release

### File List

| File | Action | Description |
|------|--------|-------------|
| `hacs.json` | Create | HACS repository metadata |
| `info.md` | Create | Integration information for HACS |
| `.github/workflows/release.yml` | Create | Automated release workflow with semver and changelog |
| `README.md` | Create | Added HACS installation instructions |
| `manifest.json` | Inspect | Verified HACS compliance (version should be 1.0.0 for release) |

## Change Log
- 2026-02-21: Story created from Epic 4
- 2026-02-21: Implementation completed - HACS config files, release workflow, and README created
- 2026-02-21: Story Acceptance — CHANGES_REQUESTED (2 blocking items)