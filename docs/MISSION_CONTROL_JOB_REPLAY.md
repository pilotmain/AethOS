# FIX 137 — Mission Control job replay view

Read-only step-by-step playback answering **“how did we get here?”** without execution controls.

## Invariant

- Derived from FIX 136 evidence bundle data only
- `mutation_performed: false` on every response
- **No rerun button** — navigation is Previous/Next step only
- No deploy, restart, merge, or execute controls

## Replay step model

Each step includes:

| Field | Purpose |
|-------|---------|
| `state_before` / `state_after` | Mission state at transition |
| `receipts` | Matched durable receipts |
| `gates` | Governance gate snapshot |
| `blockers` | Active blockers at transition |
| `approvals` | Approval status at transition |

Sources merged and sorted: software delivery plan events, cross-lane timeline, UI approval audits, tracked jobs.

## API

```http
GET /api/v1/mission-control/job-replay?session_id=<session>&job_id=<optional>&format=json|summary|both
```

| `format` | Response |
|----------|----------|
| `json` | `{ ok, replay: { steps[], final_state } }` |
| `summary` | `{ ok, summary_markdown }` |
| `both` | Full replay + markdown summary |

## UI

Sidebar: **Job Replay** (`mission-job-replay`)

- Step list + detail panel
- Previous step / Next step navigation
- Optional job id focus filter
- **Export replay summary** (Markdown download)

## Deep links (FIX 137B)

Jump from observability surfaces into a specific replay step (read-only navigation only).

| Source | Link ref pattern |
|--------|------------------|
| Cross-lane timeline | `timeline:{lane}:{action}:{timestamp}` |
| UI approval audit | `audit:{approval_id}` |
| Evidence receipt | `evidence:{recorded_at}:{phase}:{source_file}` |
| Mission start (post-export) | `mission:start` |

**URL params:** `mc_view=mission-job-replay`, `mc_link=…`, `mc_step=…`, `mc_job=…`

```http
GET /api/v1/mission-control/job-replay/resolve?session_id=<session>&link=<ref>
```

UI: **View in replay →** on timeline rows, audit rows, and drilldown receipts.

## Governed rerun planning (FIX 138)

From replay, **Show governed rerun plan** loads a read-only planning artifact (eligibility, blast radius, blockers, exact phrases — all non-executable). See [MISSION_CONTROL_RERUN_PLANNING.md](./MISSION_CONTROL_RERUN_PLANNING.md).

## Tests

```bash
pytest tests/test_mission_control_job_replay.py tests/test_mission_control_job_replay_deep_link.py -q
```
