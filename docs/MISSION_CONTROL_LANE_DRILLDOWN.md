# FIX 131 — Mission Control lane drilldown (read-only)

Deep operational introspection per lane without leaving Mission Control.

## Scope

Operators can inspect per lane:

- Lane state
- Governance gates
- Approvals (status only — no approve buttons)
- Timelines
- Durable receipts
- Verification evidence
- Rollback posture
- Blockers
- Execution contracts
- Agent collaboration findings
- Audit trails

**No** execute, deploy, restart, or approval mutation controls.

## API

```
GET /api/v1/mission-control/cross-lane/lane/{lane_id}/drilldown?session_id=<id>
```

`lane_id` is one of the FIX 128 observed lanes (`software_delivery`, `railway_orchestration`, etc.).

## UI

Mission Control → Cross-Lane Control → select a timeline item, attention item, or lane card to open the drilldown panel.

## Tests

```bash
pytest tests/test_mission_control_lane_drilldown.py -q
```
