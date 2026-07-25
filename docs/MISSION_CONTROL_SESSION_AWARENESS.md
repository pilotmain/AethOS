# FIX 130 — Mission Control session awareness + operator context

Extends FIX 129 read-only cross-lane UI with real session binding and operator-facing context.

## Behavior

- **Session id** — uses the same `sessionStorage` key as Chat (`getOrCreateChatSessionId`), passed to `GET /api/v1/mission-control/cross-lane/snapshot?session_id=…`
- **Operator context bar** — session, operator mode (from Mission Control nav), channel, correlation/plan when present
- **Timeline linking** — timeline and attention items focus a lane: scroll to lane card + inline lane detail panel (read-only)
- **States** — context skeleton, loading, error with retry, empty session snapshot

## Still out of scope

- Approve / deploy / restart / execute controls
- Mutation buttons

## Modules

| Path | Role |
|------|------|
| `web/lib/missionControl/operatorSession.ts` | Session hydration + operator context |
| `web/lib/missionControl/crossLaneLaneNavigation.ts` | Lane anchors, detail extraction, scroll |
| `web/components/missionControl/CrossLaneOperationsPanel.tsx` | UI |

## Tests

```bash
cd web && npm test -- crossLaneLaneNavigation
pytest tests/test_mission_control_cross_lane_api.py -q
```
