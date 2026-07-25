# FIX 136 — Mission Control evidence bundle export

Read-only operator evidence export for reviews, demos, incident review, and compliance.

## Invariant

**Export never mutates.** No approval execution, deploy, restart, merge, or provider mutation controls.

## Contents

Each bundle aggregates (session-scoped, optional `job_id` focus):

| Section | Source |
|---------|--------|
| Mission summary | Cross-lane snapshot + correlation/plan ids |
| Timeline | Unified timeline + tracked job events |
| Receipts | Lane drilldown receipt sections |
| Approvals | Pending inbox + UI approval audit |
| Blockers | Attention queue + inbox forbidden capabilities |
| Verification | Software delivery drilldown verification sections |
| Audit | UI audits + route diagnostics drilldown |
| Lane drilldowns | All observed lanes (batch server-side) |
| Jobs | Tracked jobs for session |
| Job evidence | Provider evidence bundles per job |
| Operation lifecycle | Session-filtered lifecycle index |
| Incident links | Snapshot incident linkage |

Secrets are redacted (`api_key`, `token`, `password`, etc.) before export.

## API

```http
GET /api/v1/mission-control/evidence-bundle?session_id=<session>&format=json|markdown|both&job_id=<optional>
```

| `format` | Response |
|----------|----------|
| `json` | `{ ok, read_only, bundle }` |
| `markdown` | `{ ok, read_only, markdown }` |
| `both` | `{ ok, bundle, markdown }` |

## UI

**Cross-lane operations** panel:

- **Export JSON** — downloadable structured bundle
- **Export Markdown** — human-readable report for stakeholders

## Tests

```bash
pytest tests/test_mission_control_evidence_bundle.py -q
```

## Modules

- `aethos_core/mission_control/evidence_bundle/evidence_bundle_service.py`
- `aethos_core/mission_control/evidence_bundle/evidence_bundle_renderer.py`
- `web/lib/missionControl/missionControlEvidenceBundleApi.ts`
