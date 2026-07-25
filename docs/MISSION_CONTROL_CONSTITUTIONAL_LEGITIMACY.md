# FIX 161 — Constitutional Legitimacy + Institutional Trust (constitutional legitimacy cognition)

**Reason about institutional legitimacy, stakeholder trust continuity, and governance credibility over time** — legitimacy cognition without autonomous enforcement, public trust manipulation, or authority expansion.

## Invariant

```text
constitutional_legitimacy → audit + trust models → constitutional legitimacy cognition
NO autonomous legitimacy enforcement · NO public trust manipulation · NO constitutional authority expansion · NO sovereignty delegation
```

## Legitimacy sections

| Section | Purpose |
|---------|---------|
| Institutional trust continuity analysis | Long-horizon institutional trust continuity |
| Governance legitimacy indicators | Governance legitimacy indicator catalog |
| Stakeholder confidence reasoning | Stakeholder confidence dimension analysis |
| Constitutional credibility drift detection | Credibility drift against legitimacy baseline |
| Governance trust fragmentation analysis | Trust fragmentation advisory analysis |
| Institutional confidence scoring | Advisory institutional confidence scoring |
| Legitimacy continuity tracking | Legitimacy continuity record tracking |
| Constitutional participation health | Constitutional participation health signals |
| Governance transparency trust analysis | Transparency-trust linkage analysis |
| Institutional credibility reconstruction | Credibility reconstruction advisory |

## Record kinds

`trust_continuity_note`, `legitimacy_indicator`, `stakeholder_confidence_note`, `credibility_drift_signal`, `legitimacy_tracking_record`

## Chat

```text
show constitutional legitimacy
constitutional legitimacy
institutional trust
legitimacy confidence: <stakeholder confidence note>
legitimacy trust: <trust continuity note>
```

Rejected: `autonomous legitimacy enforcement`, `public trust manipulation`, `constitutional authority expansion`.

## API

```http
GET /api/v1/mission-control/constitutional-legitimacy?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/constitutional-legitimacy/record
```

## UI

**Cross-lane operations** → **Constitutional legitimacy**

## Tests

```bash
pytest tests/test_mission_control_constitutional_legitimacy.py -q
```

## Related

- [FIX 162 — Constitutional pluralism + governance perspective](./MISSION_CONTROL_CONSTITUTIONAL_PLURALISM.md)
- [FIX 160 — Constitutional audit + public accountability](./MISSION_CONTROL_CONSTITUTIONAL_AUDIT.md)
- [FIX 156 — Institutional identity + constitutional intent](./MISSION_CONTROL_INSTITUTIONAL_IDENTITY.md)
