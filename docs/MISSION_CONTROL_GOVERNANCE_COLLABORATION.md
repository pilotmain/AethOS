# FIX 149 — Multi-Operator Governance Collaboration (institutional continuity)

**Structured collaborative governance between multiple human operators** — continuity across teams and roles without delegated execution authority.

## Invariant

```text
governance_collaboration → deliberation + collaboration records → multi-operator continuity
NO delegated execution · NO automatic quorum approval · NO autonomous organizational decisions
```

## Collaboration sections

| Section | Purpose |
|---------|---------|
| Named reviewers | Distinct human reviewers participating |
| Role-aware deliberation | Participation by reviewer role |
| Quorum-aware discussion | Advisory quorum tracking (does not auto-approve) |
| Review ownership | Explicit review ownership records |
| Delegated review requests | Review handoff requests (not authority delegation) |
| Reviewer assignments | Named role assignments |
| Reviewer acknowledgments | Human acknowledgment of review completion |
| Governance handoff tracking | Operator-to-operator handoffs |
| Unresolved concern escalation | Escalated concerns requiring attention |
| Decision participation graph | Reviewers ↔ deliberation participation graph |

Collaboration record writes persist **institutional continuity only**.

## Record kinds

`named_reviewer`, `reviewer_assignment`, `reviewer_acknowledgment`, `review_ownership`, `delegated_review_request`, `governance_handoff`, `unresolved_concern_escalation`, `role_deliberation`, `quorum_discussion`

## Reviewer roles

`primary_reviewer`, `secondary_reviewer`, `observer`, `escalation_owner`, `mission_owner`

## Chat

```text
show governance collaboration
multi-operator governance
collaboration assign: alice owns readiness review
collaboration acknowledge: reviewed pending approvals
collaboration handoff: to bob for secondary review
```

Rejected: `auto quorum approve`, `delegated execution`.

## API

```http
GET /api/v1/mission-control/governance-collaboration?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/governance-collaboration/record
```

## UI

**Cross-lane operations** → **Governance collaboration**

## Related

- [FIX 150 — Governance role architecture + trust boundaries](./MISSION_CONTROL_GOVERNANCE_ROLE_ARCHITECTURE.md)

## Tests

```bash
pytest tests/test_mission_control_governance_collaboration.py -q
```

## Related

- [FIX 148 — Governance deliberation workspace](./MISSION_CONTROL_GOVERNANCE_DELIBERATION.md)
- [FIX 147 — Mission readiness review board](./MISSION_CONTROL_MISSION_READINESS_REVIEW.md)
