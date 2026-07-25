# FIX 160 — Constitutional Audit + Public Accountability (constitutional accountability cognition)

**Make the constitutional cognition stack inspectable, explainable, and accountable** — audit cognition without autonomous disclosure, public communication authority, or governance enforcement.

## Invariant

```text
constitutional_audit → ethics + full stack linkage → constitutional accountability cognition
NO autonomous disclosure · NO public communication authority · NO governance enforcement · NO policy mutation
```

## Audit sections

| Section | Purpose |
|---------|---------|
| Constitutional audit reports | Full-stack constitutional audit reports |
| Traceable reasoning summaries | Traceable bounded-cognition reasoning summaries |
| Doctrine/ethics/existential linkage | Cross-layer constitutional linkage map |
| Recommendation explanations | "Why did AethOS recommend this?" explanations |
| Accountability records | Human governance accountability records |
| Human-readable governance evidence bundles | Operator accountability evidence bundles |
| Public-safe accountability summaries | Redacted public-safe disclosure summaries |
| Internal vs external disclosure boundaries | Disclosure boundary definitions |
| Constitutional transparency scoring | Advisory transparency scoring |
| Audit trail integrity checks | Audit trail integrity verification |

## Record kinds

`audit_report`, `reasoning_summary`, `accountability_record`, `recommendation_explanation`, `disclosure_boundary_note`

## Chat

```text
show constitutional audit
constitutional audit
public accountability
audit explanation: <recommendation explanation>
audit accountability: <accountability note>
```

Rejected: `autonomous disclosure`, `public communication authority`, `governance enforcement`.

## API

```http
GET /api/v1/mission-control/constitutional-audit?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/constitutional-audit/record
```

## UI

**Cross-lane operations** → **Constitutional audit**

## Tests

```bash
pytest tests/test_mission_control_constitutional_audit.py -q
```

## Related

- [FIX 161 — Constitutional legitimacy + institutional trust](./MISSION_CONTROL_CONSTITUTIONAL_LEGITIMACY.md)
- [FIX 159 — Constitutional ethics + institutional moral reasoning](./MISSION_CONTROL_CONSTITUTIONAL_ETHICS.md)
- [FIX 136 — Evidence bundle export](./MISSION_CONTROL_EVIDENCE_BUNDLE_EXPORT.md)
