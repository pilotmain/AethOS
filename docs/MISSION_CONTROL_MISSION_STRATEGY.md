# FIX 145 — Mission Strategy Layer (read-only strategic reasoning)

**Strategic cognition without strategic autonomy** — long-horizon operational reasoning composed from memory, insights, and simulations.

## Invariant

```text
mission_strategy → operational memory + cross-session + insights + simulation → strategic analysis
NO autonomous planning · NO reprioritization · NO organizational self-direction · NO policy mutation
```

## Strategic sections

| Section | Purpose |
|---------|---------|
| Long-running mission themes | Recurring plans, gates across sessions |
| Operational drift | Health degradation, blocker elevation, approval queue drift |
| Strategic bottlenecks | Cross-session blockers + approval bottlenecks |
| Mission outcome comparison | Ancestry depth, completion latency |
| Governance maturity priorities | Simulation-informed study recommendations |
| Operational hardening areas | Verification gaps, graph depth |
| Unstable rollout patterns | High-risk rollout + lineage signals |
| Organizational risk concentration | Composite risk score |
| High-friction mission archetypes | Elevated friction + long-running plans |

All recommendations: `executable: false`.

## Chat

```text
show mission strategy
strategic operational reasoning
operational drift
governance maturity priorities
```

Rejected: `autonomous plan`, `auto reprioritize`, `self-direct`.

## API

```http
GET /api/v1/mission-control/mission-strategy?session_id=<session>&format=json|markdown|both
```

## UI

**Cross-lane operations** → **Mission strategy**

## Related

- [FIX 146 — Coordinated mission orchestration](./MISSION_CONTROL_MISSION_ORCHESTRATION.md)

## Tests

```bash
pytest tests/test_mission_control_mission_strategy.py -q
```
