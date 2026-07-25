# FIX 142 — Operator Recommendations + Contextual Guidance

**Operational copiloting** built on FIX 141 semantic intelligence — not autonomous operation.

## Invariant

```text
operator_guidance → snapshot + inbox + memory + knowledge spaces + replay + rerun plan
→ structured recommendations (executable: false, operator_approval_required: true)
NO autonomous execution · NO automatic mutation planning
```

## Guidance sections

| Section | Purpose |
|---------|---------|
| Likely next governed steps | Pending UI-eligible gates and delivery stages |
| Historical mitigations | FIX 141 seen-before and historical context |
| Recurring blocker resolutions | Session + semantic blocker matches |
| Relevant incidents & PRs | Production + delivery context |
| Rollout caution | Caution level from incidents and rollout stage |
| Verification gaps | Missing or present verification evidence |
| Approval sequencing | Severity-ordered gate sequence (discretion) |
| Replay & rerun review targets | FIX 137/138 review pointers |

Every recommendation includes:

- `executable: false`
- `operator_approval_required: true`
- optional `suggested_phrase` (non-executable chat hint)

## Chat

```text
show operator guidance
what should I do next
contextual operational guidance
suggest next governed steps
approval sequencing
```

Rejected: `auto execute recommendations`, `run this for me`.

## API

```http
GET /api/v1/mission-control/operator-guidance?session_id=<session>&focus=<optional>&format=json|markdown|both
```

## UI

**Cross-lane operations** → **Operator guidance**

## Tests

```bash
pytest tests/test_mission_control_operator_guidance.py -q
```

## Related (FIX 143)

Meta-governance insights analyze how the governance system itself behaves. See [MISSION_CONTROL_GOVERNANCE_INSIGHTS.md](./MISSION_CONTROL_GOVERNANCE_INSIGHTS.md).
