# FIX 157 — Institutional External Relations + Constitutional Boundary (external-relations cognition)

**Formalize how AethOS constitutionally interacts with external systems and institutions** — boundary cognition without autonomous negotiation, provider alignment, or sovereignty delegation.

## Invariant

```text
institutional_external_relations → institutional identity + boundary models → external-relations cognition
NO autonomous external negotiation · NO autonomous provider alignment · NO self-directed institutional diplomacy · NO sovereignty delegation
```

## External relations sections

| Section | Purpose |
|---------|---------|
| External provider relationship models | Governed provider relationship catalog |
| Constitutional boundary definitions | Enduring constitutional boundary definitions |
| External trust classifications | Advisory trust classification tiers |
| Ecosystem dependency lineage | Provider dependency lineage |
| External governance interaction policies | Interaction policy advisory records |
| Provider sovereignty boundaries | Per-provider sovereignty boundary analysis |
| Constitutional interoperability analysis | Internal-external interoperability checks |
| Institutional dependency risk analysis | Ecosystem dependency risk signals |
| External influence drift detection | External influence on institutional values |
| Cross-system trust continuity | Cross-system trust continuity signals |

## Record kinds

`provider_relationship`, `boundary_definition`, `trust_classification`, `dependency_lineage`, `interaction_policy`, `influence_observation`

## Chat

```text
show external relations
institutional external relations
constitutional boundary
external provider: <relationship description>
external trust: <classification note>
```

Rejected: `autonomous external negotiation`, `sovereignty delegation`, `self-directed institutional diplomacy`.

## API

```http
GET /api/v1/mission-control/institutional-external-relations?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/institutional-external-relations/record
```

## UI

**Cross-lane operations** → **External relations**

## Tests

```bash
pytest tests/test_mission_control_institutional_external_relations.py -q
```

## Related

- [FIX 158 — Institutional existential risk + continuity preservation](./MISSION_CONTROL_INSTITUTIONAL_EXISTENTIAL_RISK.md)
- [FIX 156 — Institutional identity + constitutional intent](./MISSION_CONTROL_INSTITUTIONAL_IDENTITY.md)
- [FIX 150 — Governance role architecture + trust boundaries](./MISSION_CONTROL_GOVERNANCE_ROLE_ARCHITECTURE.md)
