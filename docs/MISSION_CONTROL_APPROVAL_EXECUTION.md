# FIX 133 — Mission Control approval execution (governed UI)

First narrowly-scoped mutation capability in Mission Control: **approval only**, routed through chat governance.

## Invariant

**Mission Control UI never bypasses chat governance routes.**

The UI builds the same operator message (command prefix + exact approval phrase(s)) and calls `resolve_chat_turn`. Lane services validate phrases and record receipts as if typed in chat.

## Eligible gates (UI Approve button)

- `planning_approved`
- `branch_create`
- `patch_proposal_approved`
- `workspace_apply`
- `github_preflight_approved`

## View-only in inbox (chat required)

- `branch_push_completed` — phrases coupled to GitHub push mutation (125H)
- `github_pr_opened` — phrases coupled to PR open mutation (125I)
- `governed_execution` job mutations — out of scope (no Railway / execute controls)

## API

```
POST /api/v1/mission-control/approval-inbox/execute
{ "session_id": "...", "inbox_id": "..." }
```

Writes audit record under `data/mission_control_ui_approval_audit/`.

## Tests

```bash
pytest tests/test_mission_control_approval_execution.py tests/test_mission_control_approval_inbox.py -q
```
