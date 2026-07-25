# FIX 156 — Institutional Identity + Constitutional Intent (institutional identity cognition)

**Preserve and reason about the enduring institutional identity and constitutional intent of AethOS governance over time** — identity cognition without autonomous redirection, mission authorship, or constitutional rewriting.

## Invariant

```text
institutional_identity → governance evolution + identity records → enduring identity cognition
NO autonomous institutional redirection · NO self-authored mission changes · NO automatic constitutional rewriting · NO governance sovereignty delegation
```

## Identity sections

| Section | Purpose |
|---------|---------|
| Institutional mission identity records | Enduring mission identity statements |
| Constitutional intent lineage | Intent lineage across institutional eras |
| Operational philosophy continuity | Enduring operational philosophy |
| Governance purpose preservation | Purpose preservation advisory signals |
| Institutional value drift detection | Value drift against mission identity |
| Constitutional mission alignment | Mission-constitutional alignment checks |
| Organizational identity continuity | Identity continuity across epochs |
| Doctrine-purpose consistency | Doctrine alignment with enduring purpose |
| Constitutional intent reconstruction | Reconstructed intent from lineage + records |
| Institutional narrative continuity | Enduring institutional narrative |

## Record kinds

`mission_identity`, `constitutional_intent`, `philosophy_record`, `purpose_preservation`, `identity_continuity`, `narrative_continuity`

## Chat

```text
show institutional identity
constitutional intent
mission identity
identity mission: <mission identity statement>
identity intent: <constitutional intent statement>
```

Rejected: `autonomous institutional redirection`, `self-authored mission`, `automatic constitutional rewriting`.

## API

```http
GET /api/v1/mission-control/institutional-identity?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/institutional-identity/record
```

## UI

**Cross-lane operations** → **Institutional identity**

## Tests

```bash
pytest tests/test_mission_control_institutional_identity.py -q
```

## Related

- [FIX 157 — Institutional external relations + constitutional boundary](./MISSION_CONTROL_INSTITUTIONAL_EXTERNAL_RELATIONS.md)
- [FIX 155 — Governance evolution + institutional continuity](./MISSION_CONTROL_GOVERNANCE_EVOLUTION.md)
- [FIX 151 — Governance doctrine + policy charter](./MISSION_CONTROL_GOVERNANCE_DOCTRINE.md)
