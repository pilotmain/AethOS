# FIX 159 — Constitutional Ethics + Institutional Moral Reasoning (constitutional ethical cognition)

**Reason about institutional ethical continuity and constitutional value conflicts without granting moral sovereignty** — ethical cognition without autonomous moral authority, self-authored ethics, or value enforcement.

## Invariant

```text
constitutional_ethics → existential risk + value models → constitutional ethical cognition
NO autonomous moral authority · NO self-authored ethics · NO constitutional override · NO value-enforcement authority
```

## Ethics sections

| Section | Purpose |
|---------|---------|
| Constitutional ethics records | Enduring constitutional value records |
| Value-conflict reasoning | Value conflict pattern analysis |
| Institutional moral tradeoff analysis | Moral tradeoff advisory analysis |
| Mission-vs-risk ethical tension analysis | Mission pressure vs existential risk tension |
| Constitutional ethics continuity | Ethics continuity across records and precedent |
| Long-horizon value preservation | Long-horizon institutional value preservation |
| Ethical ambiguity surfacing | Ethical ambiguity surfacing for human deliberation |
| Institutional moral precedent analysis | Moral precedent advisory analysis |
| Constitutional value drift detection | Value drift against constitutional intent |
| Ethical coherence scoring | Advisory ethical coherence scoring |

## Record kinds

`ethics_record`, `value_conflict_note`, `moral_tradeoff`, `ethical_tension_observation`, `value_preservation_note`, `moral_precedent`

## Chat

```text
show constitutional ethics
constitutional ethics
moral tradeoff
ethical conflict: <value conflict note>
ethical preservation: <value preservation note>
```

Rejected: `autonomous moral authority`, `self-authored ethics`, `value enforcement authority`.

## API

```http
GET /api/v1/mission-control/constitutional-ethics?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/constitutional-ethics/record
```

## UI

**Cross-lane operations** → **Constitutional ethics**

## Tests

```bash
pytest tests/test_mission_control_constitutional_ethics.py -q
```

## Related

- [FIX 160 — Constitutional audit + public accountability](./MISSION_CONTROL_CONSTITUTIONAL_AUDIT.md)
- [FIX 158 — Institutional existential risk + continuity preservation](./MISSION_CONTROL_INSTITUTIONAL_EXISTENTIAL_RISK.md)
- [FIX 156 — Institutional identity + constitutional intent](./MISSION_CONTROL_INSTITUTIONAL_IDENTITY.md)
