# FIX 146 — Coordinated Mission Orchestration (read-only coordination cognition)

**Mission-level orchestration cognition without execution** — cross-lane coordination reasoning composed from snapshot, replay, strategy, and governance state.

## Invariant

```text
mission_orchestration → cross-lane snapshot + rerun plan + inbox + strategy + insights → coordination analysis
NO autonomous sequencing · NO autonomous approval batching · NO autonomous promotion/deploy
```

## Orchestration sections

| Section | Purpose |
|---------|---------|
| Mission dependency graph | Mission root, lanes, gates, stages, replay steps |
| Governed stage orchestration | Current/upcoming delivery loop stages |
| Lane synchronization visibility | Per-lane sync posture vs mission |
| Blocked-by relationships | Gates, incidents, approvals blocking progress |
| Upstream/downstream mission effects | Cross-lane dependency effects |
| Orchestration readiness scoring | Composite readiness score |
| Operator sequencing recommendations | Governed step ordering suggestions |
| Coordinated approval batching recommendations | Review-batch hints (operator still approves each gate) |
| Cross-lane mission health | Per-lane health summary |

All recommendations: `executable: false`.

## Chat

```text
show mission orchestration
orchestration readiness
mission dependency graph
lane synchronization
operator sequencing
```

Rejected: `autonomous sequencing`, `auto batch approve`, `autonomous deploy`.

## API

```http
GET /api/v1/mission-control/mission-orchestration?session_id=<session>&format=json|markdown|both
```

## UI

**Cross-lane operations** → **Mission orchestration**

## Related

- [FIX 147 — Mission readiness review board](./MISSION_CONTROL_MISSION_READINESS_REVIEW.md)

## Tests

```bash
pytest tests/test_mission_control_mission_orchestration.py -q
```

## Related

- [FIX 145 — Mission strategy](./MISSION_CONTROL_MISSION_STRATEGY.md)
- [FIX 128 — Cross-lane observability](./MISSION_CONTROL_CROSS_LANE_OBSERVABILITY.md)
