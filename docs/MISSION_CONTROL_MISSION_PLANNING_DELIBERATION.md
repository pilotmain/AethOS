# FIX 165 — Mission Planning Multi-Agent Deliberation (bounded agent analysis)

**Assign bounded agent roles to analyze mission planning options and produce a consolidated recommendation** — analysis only, no execution authority or autonomous path selection.

## Invariant

```text
mission_planning_deliberation → mission_planning + bounded agents → deliberation analysis
NO autonomous execution · NO autonomous approval · NO autonomous lane selection · NO autonomous PR creation · NO Railway mutation · NO autonomous merge
```

## Bounded agents

| Agent | Focus |
|-------|--------|
| PlannerAgent | What institutional paths exist? |
| RiskAgent | What can go wrong? |
| ConstitutionalAgent | What constitutional tensions exist? |
| DeliveryAgent | What execution lanes would be touched? |
| VerificationAgent | What evidence is missing? |
| SynthesisAgent | Summarize multi-agent findings for human review |

**No ExecutorAgent** in FIX 165.

## Deliberation sections

| Section | Purpose |
|---------|---------|
| PlannerAgent analysis | Path analysis from mission planning options |
| RiskAgent analysis | Risks, blockers, and do-not-do paths |
| ConstitutionalAgent analysis | Constitutional tradeoffs from planning |
| DeliveryAgent analysis | Lane touch mapping advisory |
| VerificationAgent analysis | Required approvals and evidence gaps |
| SynthesisAgent summary | Consolidated agent findings |
| Multi-agent deliberation map | Role catalog and completeness |
| Consolidated recommendation | Advisory recommendation for human path selection |
| Deliberation integrity scoring | Advisory deliberation completeness scoring |

## Record kinds

`planner_analysis_note`, `risk_analysis_note`, `constitutional_analysis_note`, `delivery_analysis_note`, `verification_analysis_note`, `synthesis_summary_note`, `deliberation_record`

## Chat

```text
show planning deliberation
multi-agent deliberation
consolidated recommendation
deliberation planner: <planner analysis note>
deliberation synthesis: <synthesis summary note>
```

Rejected: `autonomous execution`, `autonomous approval`, `autonomous lane selection`, `mutate railway`, `autonomous merge`.

## API

```http
GET /api/v1/mission-control/mission-planning-deliberation?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/mission-planning-deliberation/record
```

## UI

**Cross-lane operations** → **Planning deliberation**

## Tests

```bash
pytest tests/test_mission_control_mission_planning_deliberation.py -q
```

## Related

- [FIX 166 — Human decision board + action selection](./MISSION_CONTROL_HUMAN_DECISION_BOARD.md)
- [FIX 164 — Mission planning + institutional action cognition](./MISSION_CONTROL_MISSION_PLANNING.md)
- [FIX 127 — Software delivery bounded multi-agent roles](../docs/SOFTWARE_DELIVERY_MULTI_AGENT_LANE.md)
