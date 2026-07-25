# FIX 141 — Mission Knowledge Spaces + Semantic Retrieval

Adds **semantic operational retrieval** on top of FIX 140 organizational memory — the beginning of **organizational operational intelligence** (not just storage).

## Invariant

```text
knowledge_spaces → index persisted + live docs → semantic rank → recommendations only
NO autonomous action · NO automatic mutation planning · NO adaptation
```

## Knowledge spaces

Mission-centric spaces keyed by:

- `mission:plan:{plan_id}`
- `mission:correlation:{correlation_id}`
- `session:{session_id}`
- `organizational:incidents` / `organizational:rollouts` (global journals)

## Searchable categories

incidents, blockers, approvals, PRs, verification evidence, rerun plans, agent findings, rollout history, failures, lifecycle

## Capabilities (read-only)

| Capability | Description |
|------------|-------------|
| Semantic search | Token-overlap ranking with phrase/category boosts |
| Related missions | Spaces linked by search relevance |
| Have we seen this before? | Strong-match threshold recall |
| Recommendations | Surfaced with `executable: false` |
| Operational context recall | Top hits + confidence score |

## Chat

```text
semantic search blockers and incidents
have we seen this before: open incident
mission knowledge space planning gate
related missions
operational context recall
```

Rejected: `auto execute`, `plan mutation automatically`.

## API

```http
GET /api/v1/mission-control/knowledge-spaces/search?session_id=<session>&q=<query>&format=json|markdown|both
```

Optional: `space_id`, `category`, `ingest_current=true`, `limit=20`.

## UI

**Cross-lane operations** → semantic search input + **Semantic search** button.

## Tests

```bash
pytest tests/test_mission_control_knowledge_spaces.py -q
```

## Related (FIX 142)

Structured operator recommendations compose semantic search into contextual guidance. See [MISSION_CONTROL_OPERATOR_GUIDANCE.md](./MISSION_CONTROL_OPERATOR_GUIDANCE.md).
