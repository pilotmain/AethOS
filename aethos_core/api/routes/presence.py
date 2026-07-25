# SPDX-License-Identifier: Apache-2.0
"""Presence API — ambient operational collaborator."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["presence"])


class WatchRequest(BaseModel):
    target: str
    operator_id: str = "default"


class SnoozeRequest(BaseModel):
    hours: float = 4.0


class FocusRequest(BaseModel):
    focus: str
    investigation: str = ""
    operator_id: str = "default"


@router.get("/presence/state")
def presence_state_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.presence.presence_runtime import get_presence_state

    return get_presence_state(session_id=session_id)


@router.get("/presence/feed")
def presence_feed_api(limit: int = 30) -> dict[str, Any]:
    from aethos_core.presence.collaboration_state import get_collaboration_focus
    from aethos_core.presence.operational_feed import list_feed_events
    from aethos_core.presence.presence_signal_pipeline import process_presence_signals

    processed = process_presence_signals(list_feed_events(limit=limit), focus=get_collaboration_focus())
    return {
        "ok": True,
        "feed": processed.get("events"),
        "attention": processed.get("events"),
        "clusters": processed.get("clusters"),
        "attention_quality": processed.get("attention_quality"),
    }


@router.get("/presence/incidents")
def presence_incidents_api() -> dict[str, Any]:
    from aethos_core.presence.collaboration_state import get_collaboration_focus
    from aethos_core.presence.operational_feed import list_feed_events
    from aethos_core.presence.presence_signal_pipeline import process_presence_signals

    processed = process_presence_signals(list_feed_events(limit=40), focus=get_collaboration_focus())
    return {"ok": True, "incidents": processed.get("incidents"), "clusters": processed.get("clusters")}


@router.get("/presence/clusters")
def presence_clusters_api() -> dict[str, Any]:
    from aethos_core.presence.collaboration_state import get_collaboration_focus
    from aethos_core.presence.operational_feed import list_feed_events
    from aethos_core.presence.presence_signal_pipeline import process_presence_signals

    processed = process_presence_signals(list_feed_events(limit=40), focus=get_collaboration_focus())
    return {"ok": True, "clusters": processed.get("clusters")}


@router.get("/presence/recommendations/intelligent")
def presence_intelligent_recommendations_api() -> dict[str, Any]:
    from aethos_core.presence.collaboration_state import get_collaboration_focus
    from aethos_core.presence.operational_feed import list_feed_events
    from aethos_core.presence.presence_signal_pipeline import process_presence_signals

    processed = process_presence_signals(list_feed_events(limit=40), focus=get_collaboration_focus())
    return {"ok": True, "recommendations": processed.get("recommendations")}


@router.get("/presence/attention/quality")
def presence_attention_quality_api() -> dict[str, Any]:
    from aethos_core.presence.collaboration_state import get_collaboration_focus
    from aethos_core.presence.operational_feed import list_feed_events
    from aethos_core.presence.presence_signal_pipeline import process_presence_signals

    processed = process_presence_signals(list_feed_events(limit=40), focus=get_collaboration_focus())
    return {
        "ok": True,
        "attention": processed.get("events"),
        "attention_quality": processed.get("attention_quality"),
    }


@router.get("/presence/timeline")
def presence_timeline_api(window_hours: int = 48) -> dict[str, Any]:
    from aethos_core.presence.replay_bridge import build_presence_timeline, list_presence_timelines

    timeline = build_presence_timeline(window_hours=window_hours)
    return {"ok": True, "timeline": timeline, "recent": list_presence_timelines(limit=5)}


@router.get("/presence/timeline/{timeline_id}")
def presence_timeline_detail_api(timeline_id: str) -> dict[str, Any]:
    from aethos_core.presence.replay_bridge import get_presence_timeline

    row = get_presence_timeline(timeline_id)
    if not row:
        raise HTTPException(status_code=404, detail="timeline_not_found")
    return {"ok": True, "timeline": row}


@router.get("/presence/attention")
def presence_attention_api() -> dict[str, Any]:
    from aethos_core.presence.presence_runtime import get_presence_state

    state = get_presence_state()
    return {"ok": True, "attention": state.get("attention"), "attention_quality": state.get("attention_quality")}


@router.get("/presence/watchers")
def presence_watchers_api() -> dict[str, Any]:
    from aethos_core.presence.watch_mode import list_watchers

    return {"ok": True, "watchers": list_watchers()}


@router.get("/presence/memory")
def presence_memory_api(window_hours: int = 48) -> dict[str, Any]:
    from aethos_core.presence.presence_memory import presence_memory_snapshot

    return {"ok": True, "memory": presence_memory_snapshot(window_hours=window_hours)}


@router.get("/presence/focus")
def presence_focus_api(operator_id: str = "default") -> dict[str, Any]:
    from aethos_core.presence.collaboration_state import get_collaboration_focus, list_collaboration_sessions

    return {
        "ok": True,
        "focus": get_collaboration_focus(operator_id=operator_id),
        "sessions": list_collaboration_sessions(),
    }


@router.post("/presence/cycle")
def presence_cycle_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.presence.presence_runtime import run_presence_cycle

    return run_presence_cycle(session_id=session_id, channel="api")


@router.post("/presence/watch")
def presence_watch_api(body: WatchRequest) -> dict[str, Any]:
    from aethos_core.presence.watch_mode import register_watcher

    result = register_watcher(target=body.target, operator_id=body.operator_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "watch_failed")
    return result


@router.post("/presence/focus")
def presence_set_focus_api(body: FocusRequest) -> dict[str, Any]:
    from aethos_core.presence.collaboration_state import start_collaboration_session

    session = start_collaboration_session(
        operator_id=body.operator_id,
        focus=body.focus,
        investigation=body.investigation,
    )
    return {"ok": True, "session": session}


@router.post("/presence/recommendation/{recommendation_id}/dismiss")
def presence_dismiss_recommendation_api(recommendation_id: str) -> dict[str, Any]:
    from aethos_core.presence.presence_runtime import dismiss_presence_recommendation

    result = dismiss_presence_recommendation(recommendation_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "dismiss_failed")
    return result


@router.post("/presence/recommendation/{recommendation_id}/snooze")
def presence_snooze_recommendation_api(recommendation_id: str, body: SnoozeRequest | None = None) -> dict[str, Any]:
    from aethos_core.presence.presence_runtime import snooze_presence_recommendation

    hours = body.hours if body else 4.0
    result = snooze_presence_recommendation(recommendation_id, hours=hours)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "snooze_failed")
    return result
