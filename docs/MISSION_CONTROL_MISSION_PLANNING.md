# FIX 164 — Mission Planning + Institutional Action Cognition (planning cognition)

**Bridge constitutional synthesis to institutional action options and human-governed lane selection** — planning cognition without execution authority or autonomous path selection.

## Invariant

```text
mission_planning → synthesis + orchestration + strategy + readiness → institutional action cognition
NO autonomous action execution · NO autonomous approval · NO auto path selection · NO Railway mutation · NO PR open/merge/deploy/restart
```

## Planning sections

| Section | Purpose |
|---------|---------|
| Action option generation | Institutional action options informed by constitutional synthesis |
| Option comparison | Compare options against orchestration readiness and strategy |
| Lane touch mapping | Map each option to lanes it would touch (advisory only) |
| Required approvals | List pending and required human approvals |
| Constitutional tradeoffs | Surface synthesis tradeoffs for planning deliberation |
| Risks and blockers | Orchestration and readiness blockers |
| Do not do paths | Explicit unsafe paths planning must never trigger |
| Operator review sequence | Recommended human review order |
| Mission action plan artifact | Consolidated planning artifact for operator review |

## Record kinds

`action_option_note`, `option_comparison_note`, `lane_mapping_note`, `required_approval_note`, `constitutional_tradeoff_note`, `risk_blocker_note`, `do_not_do_path_note`, `review_sequence_note`, `mission_action_plan_artifact`

## Chat

```text
show mission planning
mission planning
institutional action options
planning option: <action option note>
planning lane: <lane mapping note>
planning avoid: <do not do path note>
```

Rejected: `execute action`, `approve action`, `auto-select path`, `open pr`, `mutate railway`, `merge deploy restart`.

## API

```http
GET /api/v1/mission-control/mission-planning?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/mission-planning/record
```

## UI

**Cross-lane operations** → **Mission planning**

## Tests

```bash
pytest tests/test_mission_control_mission_planning.py -q
```

## Related

- [FIX 165 — Mission planning multi-agent deliberation](./MISSION_CONTROL_MISSION_PLANNING_DELIBERATION.md)
- [FIX 163 — Constitutional synthesis + institutional wisdom](./MISSION_CONTROL_CONSTITUTIONAL_SYNTHESIS.md)
- [FIX 146 — Mission orchestration](./MISSION_CONTROL_MISSION_ORCHESTRATION.md)
- [FIX 147 — Mission readiness review](./MISSION_CONTROL_MISSION_READINESS_REVIEW.md)
