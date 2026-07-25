# FIX 140 — Cross-Session Operational Memory (organizational layer)

Extends FIX 139 session-scoped relational memory with **durable multi-session persistence** — the first AethOS **organizational memory layer**.

## Invariant

```text
cross_session_memory → ingest FIX 139 graph → persist record → correlate across sessions
NO mutations · NO autonomous adaptation · NO autonomous optimization
```

## Persistence

Records stored at:

```text
aethos_core/data/mission_control_operational_memory/records/{record_id}.json
```

Each ingest snapshots a compact record (plan_id, correlation_id, PR/incident/gate keys, blockers, lineage, stats). Duplicate ingests for the same session+plan within 5 minutes update the existing record.

## Organizational capabilities (read-only)

| Capability | Description |
|------------|-------------|
| Missions across sessions | Group by plan_id / correlation_id |
| Recurring incidents | Global incident journal + persisted keys |
| PR lineage across sessions | PR keys linked to multiple sessions |
| Historical blockers | Blocker signatures with cross-session flag |
| Operator history | Durable recorded session snapshots |
| Mission ancestry | Plan-scoped record chains over time |
| Approval / risk patterns | Gate frequency and outcome counts |
| Rollout lineage | Production rollout journal timeline |
| Evidence stitching | Records sharing plan, PR, or incident keys |

## Chat

```text
show cross-session operational memory
organizational memory layer
correlate missions across sessions
operator history
cross-session memory
```

Rejected: `auto-adapt from memory`, `autonomous optimization`.

## API

```http
GET /api/v1/mission-control/operational-memory/cross-session?session_id=<session>&ingest_current=true&limit=200&format=json|markdown|both
```

`ingest_current=true` (default) builds FIX 139 graph for the focal session and persists before correlating.

## UI

**Cross-lane operations** → **Cross-session memory** (inline organizational preview).

## Tests

```bash
pytest tests/test_mission_control_cross_session_memory.py -q
```

## Related (FIX 141)

Semantic search and mission knowledge spaces index persisted organizational records. See [MISSION_CONTROL_KNOWLEDGE_SPACES.md](./MISSION_CONTROL_KNOWLEDGE_SPACES.md).
