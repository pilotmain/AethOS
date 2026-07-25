# FIX 134 — Mission Control action safety + UI approval audit

## Scope

- UI approval execution history in Mission Control
- Route / intent / gate cleared / failure reasons visible
- Copy phrase fallback for manual chat
- Replay protection for duplicate UI approvals
- Certification: no direct provider mutation APIs on MC UI path

## APIs

```
GET /api/v1/mission-control/approval-inbox/audit?session_id=&limit=
GET /api/v1/mission-control/action-safety/review
```

## Replay protection

- Successful audit for `session_id` + `inbox_id` → subsequent execute returns `replay_protected`
- Gate already satisfied → `gate_already_cleared` without re-dispatching chat

## Invariant (certified)

`execute_governed_ui_approval` only calls `resolve_chat_turn` — never GitHub/Railway mutation helpers directly.

## Tests

```bash
pytest tests/test_mission_control_approval_audit.py tests/certification/test_mission_control_ui_action_safety_certification.py -q
```
