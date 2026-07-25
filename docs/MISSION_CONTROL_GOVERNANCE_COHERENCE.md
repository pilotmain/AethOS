# FIX 153 — Governance Coherence + Constitutional Integrity (institutional coherence intelligence)

**Continuous evaluation of whether governance behavior remains coherent with institutional doctrine and topology** — recommendation-only intelligence without autonomous correction or override authority.

## Invariant

```text
governance_coherence → policy interpretation + doctrine + topology → constitutional integrity intelligence
NO automatic doctrine enforcement · NO autonomous governance correction · NO self-healing governance · NO constitutional override
```

## Coherence sections

| Section | Purpose |
|---------|---------|
| Doctrine/topology consistency analysis | Alignment between doctrine and trust topology |
| Precedent drift detection | Cross-session and confidence-based drift signals |
| Governance contradiction surfacing | Conflicts and competing readings surfaced |
| Institutional integrity scoring | Advisory integrity score (not enforcement weight) |
| Policy fragmentation analysis | Sprawl and ambiguity fragmentation signals |
| Governance principle alignment checks | Principle-to-behavior alignment verification |
| Cross-session doctrine coherence | Session vs institutional corpus comparison |
| Conflicting precedent clustering | Topic-based precedent conflict clusters |
| Trust-boundary consistency analysis | Delegation and topology boundary checks |
| Governance stability indicators | Composite stability advisory signals |

## Record kinds

`coherence_observation`, `contradiction_report`, `drift_signal`, `integrity_note`, `stability_note`

## Chat

```text
show governance coherence
constitutional integrity
precedent drift
governance stability
coherence observation: <observation text>
coherence drift: <drift signal text>
```

Rejected: `self-healing governance`, `constitutional override`, `autonomous governance correction`.

## API

```http
GET /api/v1/mission-control/governance-coherence?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/governance-coherence/record
```

## UI

**Cross-lane operations** → **Governance coherence**

## Tests

```bash
pytest tests/test_mission_control_governance_coherence.py -q
```

## Related

- [FIX 154 — Governance resilience + stress simulation](./MISSION_CONTROL_GOVERNANCE_RESILIENCE.md)
- [FIX 152 — Governance policy interpretation](./MISSION_CONTROL_GOVERNANCE_POLICY_INTERPRETATION.md)
- [FIX 151 — Governance doctrine + policy charter](./MISSION_CONTROL_GOVERNANCE_DOCTRINE.md)
