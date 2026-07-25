# FIX 138 — Governed Rerun Planning (chat-only)

Answers **“If we rerun this governed flow, what would happen?”** before any rerun execution exists.

## Invariant

```text
governed_rerun_planning → replay + evidence bundle analysis → planning artifact
NO rerun execution · NO rerun button · NO provider mutations
```

`rerun_execution_enabled` is always `false` in FIX 138.

## Plan contents

| Section | Purpose |
|---------|---------|
| Eligibility | Planning vs execution eligibility |
| Replay-derived plan | Target step, gate, link_key from FIX 137 replay |
| Blast radius | Risk tier, unlocks, remains forbidden |
| Dependencies | Prior software delivery stages required |
| Stale-state | Plan/gates advanced since target step |
| Rollback posture | Workspace rollback vs autonomous forbidden |
| Required approvals | Gates that would need phrases if recovering |
| Rerun blockers | Including `rerun_execution_disabled` |
| Mutation preview | Hypothetical stages only |
| Exact rerun phrases | Documented, `executable: false` |

## Chat

```text
show governed rerun plan
governed rerun planning
what would happen if we rerun
rerun eligibility
```

Rejected: `execute rerun now`, `trigger rerun`, `perform rerun`.

## API

```http
GET /api/v1/mission-control/rerun-plan?session_id=<session>&from_step=<n>&link_key=<ref>&format=json|markdown|both
```

## UI

**Job Replay** panel → **Show governed rerun plan** (read-only analysis for current step).

## Related (FIX 139)

Operational memory composes rerun plans into a session-scoped knowledge graph. See [MISSION_CONTROL_OPERATIONAL_MEMORY.md](./MISSION_CONTROL_OPERATIONAL_MEMORY.md).

## Tests

```bash
pytest tests/test_mission_control_rerun_plan.py -q
```
