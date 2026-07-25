# FIX 148 — Governance Deliberation Workspace (institutional governance memory)

**Collaborative decision reasoning around the Readiness Review Board** — structured deliberation without approval automation or policy mutation.

## Invariant

```text
governance_deliberation → readiness review + deliberation records → institutional memory
NO automatic approval · NO automatic rejection · NO governance mutation · NO delegated authority
```

## Workspace sections

| Section | Purpose |
|---------|---------|
| Readiness review context | FIX 147 advisory context anchor |
| Operator notes | Human-authored session notes |
| Reviewer annotations | Reviewer commentary |
| Structured concerns | Formal concern records |
| Dissent tracking | Recorded dissent |
| Rationale capture | Decision rationale |
| Alternative-path comparison | go / hold / no-go paths + recorded alternatives |
| Review checklist | Persisted human-confirmed checklist items |
| Why was this approved/rejected? | Approval/rejection rationale records |
| Governance discussion timeline | Chronological deliberation history |
| Decision justification records | Formal justification artifacts |

Deliberation record writes persist **institutional governance memory only** — not governance execution.

## Record kinds

`operator_note`, `reviewer_annotation`, `structured_concern`, `dissent`, `rationale`, `alternative_path`, `checklist_item`, `approval_rejection_rationale`, `decision_justification`

## Chat

```text
show governance deliberation
governance discussion timeline
deliberation note: <text>
deliberation concern: <text>
deliberation dissent: <text>
```

Rejected: `auto approve`, `autonomous policy`.

## API

```http
GET /api/v1/mission-control/governance-deliberation?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/governance-deliberation/record
```

POST body: `{ "session_id", "kind", "content", "author?" }` — deliberation memory only.

## UI

**Cross-lane operations** → **Governance deliberation**

## Related

- [FIX 149 — Multi-operator governance collaboration](./MISSION_CONTROL_GOVERNANCE_COLLABORATION.md)

## Tests

```bash
pytest tests/test_mission_control_governance_deliberation.py -q
```

## Related

- [FIX 147 — Mission readiness review board](./MISSION_CONTROL_MISSION_READINESS_REVIEW.md)
- [FIX 140 — Cross-session organizational memory](./MISSION_CONTROL_CROSS_SESSION_MEMORY.md)
