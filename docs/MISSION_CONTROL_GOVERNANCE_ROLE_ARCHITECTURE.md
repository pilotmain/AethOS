# FIX 150 — Governance Role Architecture + Trust Boundaries (institutional topology)

**Formalize governance roles, trust zones, escalation boundaries, and institutional authority structure** — read-only topology derived from collaboration memory and frozen contracts.

## Invariant

```text
governance_role_architecture → collaboration + frozen role taxonomy → institutional topology
NO delegated execution · NO auto-approval · NO autonomous role elevation · NO policy mutation
```

## Architecture sections

| Section | Purpose |
|---------|---------|
| Governance role taxonomy | Institutional roles + observed operators |
| Trust boundary modeling | Zone crossings and human authority requirements |
| Role capability matrix | Per-role can/cannot capabilities |
| Escalation path definitions | Default + recorded escalation paths |
| Separation-of-duty policies | Enforced SoD rules |
| Review authority scopes | Recommendation vs chat-governed vs execution scopes |
| Quorum role composition rules | Advisory quorum composition (no auto-approval) |
| Governance delegation boundaries | Review delegation vs forbidden execution delegation |
| Operator trust zones | Operators mapped to trust zones |
| Institutional responsibility maps | Review ownership and assignments |

All topology: **read-only**.

## Trust zones

`observability` → `deliberation_memory` → `collaboration_memory` → `readiness_advisory` → `chat_governed_approval` → `execution_substrate`

## Chat

```text
show governance role architecture
trust boundaries
separation-of-duty
governance topology
```

Rejected: `auto-elevate role`, `delegated execution`.

## API

```http
GET /api/v1/mission-control/governance-role-architecture?session_id=<session>&format=json|markdown|both
```

## UI

**Cross-lane operations** → **Role architecture**

## Related

- [FIX 151 — Governance doctrine + policy charter](./MISSION_CONTROL_GOVERNANCE_DOCTRINE.md)

## Tests

```bash
pytest tests/test_mission_control_governance_role_architecture.py -q
```

## Related

- [FIX 149 — Multi-operator governance collaboration](./MISSION_CONTROL_GOVERNANCE_COLLABORATION.md)
- [FIX 148 — Governance deliberation workspace](./MISSION_CONTROL_GOVERNANCE_DELIBERATION.md)
