# FIX 151 — Governance Doctrine + Policy Charter (institutional constitutionality)

**Durable institutional governance doctrine and policy continuity** — charter records, principles, precedents, and amendment proposals without autonomous policy mutation.

## Invariant

```text
governance_doctrine → role architecture + charter records → constitutional continuity
NO automatic policy mutation · NO autonomous doctrine evolution · NO self-modifying governance
```

## Doctrine sections

| Section | Purpose |
|---------|---------|
| Governance charter records | Institutional charter artifacts |
| Doctrine versioning | Version lineage (no autonomous evolution) |
| Policy rationale history | Recorded + topology-derived rationales |
| Governance principle registry | Constitutional principles |
| Institutional rule lineage | SoD and delegation rule lineage |
| Policy amendment proposals | Human-reviewed proposals only (`executable: false`) |
| Governance precedent tracking | Institutional precedents |
| Doctrine conflict detection | Amendment vs constitutional conflict signals |
| Policy freeze snapshots | Topology + recorded freeze snapshots |
| Constitutional governance references | FIX references as constitutional anchors |

## Record kinds

`governance_charter`, `doctrine_version`, `policy_rationale`, `policy_amendment_proposal`, `governance_precedent`, `constitutional_reference`, `policy_freeze_snapshot`

## Chat

```text
show governance doctrine
policy charter
governance principles
doctrine amendment: <proposal text>
doctrine precedent: <precedent text>
```

Rejected: `autonomous doctrine`, `self-modifying governance`.

## API

```http
GET /api/v1/mission-control/governance-doctrine?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/governance-doctrine/record
```

## UI

**Cross-lane operations** → **Governance doctrine**

## Tests

```bash
pytest tests/test_mission_control_governance_doctrine.py -q
```

## Related

- [FIX 152 — Governance policy interpretation + precedent application](./MISSION_CONTROL_GOVERNANCE_POLICY_INTERPRETATION.md)
- [FIX 150 — Governance role architecture](./MISSION_CONTROL_GOVERNANCE_ROLE_ARCHITECTURE.md)
- [FIX 148 — Governance deliberation](./MISSION_CONTROL_GOVERNANCE_DELIBERATION.md)
