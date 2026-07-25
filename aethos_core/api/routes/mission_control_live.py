# SPDX-License-Identifier: Apache-2.0
"""Mission Control live update endpoints — SSE + recent event replay."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["mission-control-live"])


@router.get("/mission-control/live/events")
def mission_control_live_events(replay: int = 20) -> StreamingResponse:
    from aethos_core.mission_control.live_updates.live_update_bus import sse_stream

    return StreamingResponse(
        sse_stream(replay=max(0, min(replay, 100))),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/mission-control/live/recent")
def mission_control_live_recent(limit: int = 50) -> dict[str, object]:
    from aethos_core.mission_control.live_updates.live_update_bus import recent_live_updates

    rows = recent_live_updates(limit=max(1, min(limit, 200)))
    return {"ok": True, "count": len(rows), "events": rows}


@router.post("/mission-control/live/publish")
def mission_control_live_publish(body: dict[str, object]) -> dict[str, object]:
    from aethos_core.mission_control.live_updates.live_update_bus import publish_live_update

    event_type = str(body.get("type") or "operator_note")
    payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
    event = publish_live_update(event_type=event_type, payload=dict(payload))
    return {"ok": True, "event": event}
