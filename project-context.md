# Project Context: Heimdall Battery Sentinel

## Dev Server / Home Assistant Instance

This project may be tested against a running Home Assistant instance.

- The dev server URL and HA credentials are stored in a local `.env` file at the repo root.
- **Security:** `.env` is intentionally gitignored and must never be committed.

Expected environment variables:
- `DEV_SERVER_URL`
- `HOME_ASSISTANT_USERNAME`
- `HOME_ASSISTANT_PASSWORD`

Agent guidance:
- When a workflow requires a dev server (e.g. UX review / QA), read these variables from `.env` (or the environment) and use them for authentication if needed.
- Do not print secrets into logs, story files, or reports.
