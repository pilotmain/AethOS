# Mission Control Phase 2 UI Freeze (FIX 135)

**Status:** FROZEN at FIX 135  
**Schema:** `mission_control_operator_console_v1`  
**Scope:** FIX 128–135 operator console (cross-lane + approval inbox)

---

## Objective

Freeze Mission Control as a **governed operator console**: read-only cross-lane observability plus **narrow UI approvals** that always route through chat governance. No new mutation surfaces in FIX 135.

---

## Frozen operator console

| View | Fixes | Capability |
|------|-------|------------|
| Cross-lane operations | 129–131 | Snapshot, timeline, lane drilldown |
| Approval inbox | 132–134 | Pending gates, copy phrase, governed approve, audit |

---

## Frozen invariants

1. **Read-only cross-lane** — `GET` snapshot and drilldown only; `mutation_performed` false on observability paths.
2. **Single UI mutation entry** — `POST /api/v1/mission-control/approval-inbox/execute` only.
3. **Chat governance required** — UI calls `resolve_chat_turn` with exact approval phrases; never provider SDKs.
4. **Eligible gates only** — UI Approve enabled only for planning, branch, patch, workspace apply, GitHub preflight.
5. **View-only coupled mutations** — branch push, PR open, governed execution jobs remain chat-only.
6. **Audit + replay protection** — every UI approval recorded; duplicate approvals blocked (FIX 134).
7. **Session scoped** — operator context and inbox filtered by `session_id`.
8. **No deploy/restart/merge/execute buttons** — certified absent from frozen React panels.

---

## Frozen HTTP API surface

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/mission-control/cross-lane/snapshot` | Cross-lane snapshot |
| GET | `/mission-control/cross-lane/lane/{lane_id}/drilldown` | Lane drilldown |
| GET | `/mission-control/approval-inbox` | Pending approvals |
| POST | `/mission-control/approval-inbox/execute` | Governed UI approval |
| GET | `/mission-control/approval-inbox/audit` | Approval history |
| GET | `/mission-control/action-safety/review` | Provider-path safety review |
| GET | `/mission-control/evidence-bundle` | Operator evidence export (FIX 136, read-only) |
| GET | `/mission-control/job-replay` | Job replay playback (FIX 137, read-only) |

No other `/mission-control/*` routes may be added without a contract re-freeze.

---

## Explicitly NOT included (blocked after FIX 135)

- Deploy / restart / merge buttons in operator console views
- Direct GitHub push or PR open from UI
- Railway or infrastructure mutation from UI
- Provider SDK calls from Mission Control API handlers
- Autonomous approval without exact phrases
- Bypass of replay protection or audit logging

---

## UI route ownership matrix

| View | Backend owner | API | Mode |
|------|---------------|-----|------|
| cross-lane-operations | `snapshot_service` | GET snapshot | read_only |
| cross-lane-operations | `lane_drilldown_service` | GET drilldown | read_only |
| approval-inbox | `approval_inbox_service` | GET inbox | read_only |
| approval-inbox | `approval_execution_service` | POST execute | governed_approval |
| approval-inbox | `approval_audit_service` | GET audit | read_only |
| approval-inbox | `action_safety_review` | GET action-safety/review | read_only |

Machine-readable: `MISSION_CONTROL_UI_ROUTE_MATRIX` in `mission_control_ui_freeze_contract.py`.

---

## Out of freeze scope (legacy shell)

Mission Control still contains **legacy panels** (runtime actions, Railway job controls, deployment topology labels). FIX 135 does **not** certify those for production operator use. Future action surfaces require explicit FIX series and re-freeze.

---

## Certification

```bash
pytest tests/certification/test_mission_control_ui_freeze_certification.py -q
make certify
```

Tests verify: frozen docs, frozen components, API route set, web client POST policy, action safety review, forbidden button labels.

---

## Re-freeze policy

To add UI mutation capability:

1. New FIX with threat model and chat-governance proof
2. Update `mission_control_ui_freeze_contract.py` and certification tests
3. Update operator runbook and troubleshooting
4. Re-run `make certify` with updated baselines in `aethos_phase_2_readiness_contract.py`
