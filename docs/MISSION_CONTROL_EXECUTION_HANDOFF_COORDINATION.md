# FIX 167 — Governed Execution Handoff Coordination (handoff cognition)

**Connect the recorded human decision to the correct governed execution lane** without executing anything — handoff coordination only.

## Invariant

```text
execution_handoff_coordination → human decision board → governed lane mapping
NO autonomous execution · NO autonomous approval · NO autonomous lane entry · NO PR open · NO merge/deploy · NO Railway mutation
```

## Handoff sections

| Section | Purpose |
|---------|---------|
| Selected human decision read | Read FIX 166 human selection record |
| Eligible lane mapping | Map selected path to eligible governed lanes |
| Execution handoff package | Consolidated handoff artifact for lane entry |
| Required lane gates | Gates that must pass before lane entry |
| Required approvals | Pending approvals from approval inbox |
| Remaining blockers | Orchestration and deliberation blockers |
| Forbidden actions | Actions handoff coordination must never perform |
| Next-step command sequence | Advisory operator command hints per lane |
| Handoff integrity scoring | Completeness of handoff package |

## Record kinds

`handoff_artifact`, `lane_gate_note`, `approval_requirement_note`, `blocker_note`, `forbidden_action_note`, `next_step_note`, `handoff_coordination_record`

## Chat

```text
show execution handoff
handoff package
eligible lanes
handoff artifact: <handoff package note>
handoff step: <next step note>
```

Rejected: `autonomous execution`, `autonomous approval`, `autonomous lane entry`, `open pr`, `merge deploy`, `mutate railway`.

## API

```http
GET /api/v1/mission-control/execution-handoff-coordination?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/execution-handoff-coordination/record
```

## UI

**Cross-lane operations** → **Execution handoff**

## Tests

```bash
pytest tests/test_mission_control_execution_handoff_coordination.py -q
```

## Related

- [FIX 166 — Human decision board + action selection](./MISSION_CONTROL_HUMAN_DECISION_BOARD.md)
- FIX 168 — Bounded multi-agent delivery work packages
- [FIX 164 — Mission planning + institutional action cognition](./MISSION_CONTROL_MISSION_PLANNING.md)
