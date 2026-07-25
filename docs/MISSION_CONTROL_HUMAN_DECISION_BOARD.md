# FIX 166 — Human Decision Board + Action Selection (human choice only)

**Formalize the human decision step** — record selected path, rejected paths, rationale, accepted tradeoffs and risks, and decision traceability as first-class institutional artifacts.

## Invariant

```text
human_decision_board → deliberation + planning → human choice record
NO autonomous selection · NO autonomous execution · NO autonomous approval · NO autonomous PR creation · NO autonomous merge · NO Railway mutation
```

## Decision board sections

| Section | Purpose |
|---------|---------|
| Candidate action board | Options A/B/C and hold path from mission planning |
| Human selection record | Selected path, who selected, when |
| Rejected paths analysis | Paths not chosen and why |
| Decision rationale capture | Why the path was selected |
| Accepted tradeoffs and risks | Consciously accepted tradeoffs and risks |
| Decision traceability | Evidence, agent participation, decision context |
| Decision review package | Decision, approval, and execution handoff artifacts |
| Decision integrity scoring | Advisory completeness of human decision record |

## Record kinds

`selection_record`, `rejection_note`, `rationale_note`, `tradeoff_acceptance_note`, `risk_acceptance_note`, `decision_artifact`, `approval_artifact`, `execution_handoff_artifact`

## Chat

```text
show human decision board
candidate action board
decision select: <selected path>
decision reject: <rejected path note>
decision rationale: <why this path was chosen>
decision handoff: <execution handoff artifact note>
```

Rejected: `autonomous selection`, `autonomous execution`, `auto-select path`, `system selects path`.

## API

```http
GET /api/v1/mission-control/human-decision-board?session_id=<session>&format=json|markdown|both
POST /api/v1/mission-control/human-decision-board/record
```

## UI

**Cross-lane operations** → **Human decision board**

## Tests

```bash
pytest tests/test_mission_control_human_decision_board.py -q
```

## Related

- [FIX 167 — Governed execution handoff coordination](./MISSION_CONTROL_EXECUTION_HANDOFF_COORDINATION.md)
- [FIX 165 — Mission planning multi-agent deliberation](./MISSION_CONTROL_MISSION_PLANNING_DELIBERATION.md)
- [FIX 164 — Mission planning + institutional action cognition](./MISSION_CONTROL_MISSION_PLANNING.md)
