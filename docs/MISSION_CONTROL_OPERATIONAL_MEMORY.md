# FIX 139 — Operational Memory / Knowledge Graph (read-only)

The first **AethOS operational memory substrate**: durable relational memory across missions, jobs, approvals, incidents, PRs, replay chains, verification evidence, rerun plans, agent findings, and rollout history.

## Invariant

```text
operational_memory → evidence bundle + replay + rerun plan → knowledge graph artifact
NO mutations · NO autonomous adaptation · NO rerun execution
```

`autonomous_adaptation_enabled` is always `false` in FIX 139.

## Capabilities (read-only)

| Capability | Description |
|------------|-------------|
| Correlate related executions | Group jobs and lifecycle operations by shared operation |
| Repeated failures | Surface failure signatures from timeline, jobs, replay |
| Historical blast radius | Compose from FIX 138 rerun plan or evidence blockers |
| Recurring blockers | Count blocker codes/details in session scope |
| Mission lineage | Session → plan → gates → jobs → PR chain |
| Cross-domain links | Incidents ↔ rollouts ↔ PRs ↔ approvals |
| Learning signals | Observation-only patterns (not actionable mutations) |

## Graph model

**Node kinds:** mission, job, approval, gate, incident, rollout, pr, replay_step, verification, rerun_plan, agent_finding, blocker, lifecycle, receipt

**Edge kinds:** session_contains, plan_governs, job_in_session, approval_for_gate, audit_of_approval, replay_of_timeline, rerun_plan_targets, incident_blocks, rollout_observed, dependency, lineage, correlates_with, evidence_of

## Chat

```text
show operational memory graph
mission lineage
correlate related executions
recurring blockers
repeated failures
historical blast radius
```

Rejected: `auto-adapt from memory`, `mutate from memory`.

## API

```http
GET /api/v1/mission-control/operational-memory?session_id=<session>&format=json|markdown|both
```

Optional: `job_id`, `include_replay=false`, `include_rerun_plan=false`.

## UI

**Cross-lane operations** → **Operational memory** (inline graph preview, read-only).

## Tests

```bash
pytest tests/test_mission_control_operational_memory.py -q
```

## Related (FIX 140)

Cross-session persistence and organizational correlation build on session graphs. See [MISSION_CONTROL_CROSS_SESSION_MEMORY.md](./MISSION_CONTROL_CROSS_SESSION_MEMORY.md).
