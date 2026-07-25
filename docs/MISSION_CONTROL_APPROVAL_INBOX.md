# FIX 132 — Mission Control approval inbox (view-only)

Central operator view: **“What needs my decision right now?”**

## Scope

- Aggregates pending approval gates across lanes (software delivery + governed execution jobs)
- Exact required phrase(s)
- Risk tier and blast radius
- What approval unlocks
- What remains forbidden
- Grouped by lane and severity

**Out of scope (deferred):** approve buttons, mutation execution from inbox.

## API

```
GET /api/v1/mission-control/approval-inbox?session_id=<id>
```

## UI

Mission Control → **Overview** → **Approval Inbox**

## Tests

```bash
pytest tests/test_mission_control_approval_inbox.py -q
```
