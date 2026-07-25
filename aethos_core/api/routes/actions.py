# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aethos_core.api.event_poll import safe_event_poll
from aethos_core.runtime.actions import ACTION_TYPES
from aethos_core.runtime.authority import authority

router = APIRouter(tags=["actions"])


class ProposeIn(BaseModel):
    action_type: str = Field(min_length=1, max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="api", max_length=32)


class ApproveIn(BaseModel):
    action_id: str = Field(min_length=4, max_length=64)


class DenyIn(BaseModel):
    action_id: str = Field(min_length=4, max_length=64)


def _approve_action_id(action_id: str) -> dict[str, Any]:
    try:
        action = authority.approve_action(action_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Action not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return action.to_dict()


def _deny_action_id(action_id: str) -> dict[str, Any]:
    try:
        action = authority.deny_action(action_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Action not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return action.to_dict()


@router.post("/actions/propose")
def post_propose_action(body: ProposeIn) -> dict[str, Any]:
    if body.action_type not in ACTION_TYPES:
        raise HTTPException(status_code=422, detail=f"Unknown action_type: {body.action_type}")
    try:
        action = authority.propose_action(body.action_type, body.params, source=body.source)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return action.to_dict()


@router.post("/actions/approve")
def post_approve_action(body: ApproveIn) -> dict[str, Any]:
    return _approve_action_id(body.action_id)


@router.post("/actions/{action_id}/approve")
def post_approve_action_by_id(action_id: str) -> dict[str, Any]:
    return _approve_action_id(action_id)


@router.post("/actions/deny")
def post_deny_action(body: DenyIn) -> dict[str, Any]:
    return _deny_action_id(body.action_id)


@router.post("/actions/{action_id}/deny")
def post_deny_action_by_id(action_id: str) -> dict[str, Any]:
    return _deny_action_id(action_id)


@router.get("/actions")
def get_actions() -> dict[str, Any]:
    grouped = authority.list_actions_grouped()
    total = sum(len(v) for v in grouped.values())
    return {"actions": grouped, "count": total}


@router.get("/actions/events")
def get_action_events(
    ids: str | None = None,
    session_id: str | None = None,
    since: float = 0.0,
) -> dict[str, Any]:
    """Lifecycle events for chat bridge — observational, ordered by time."""
    action_ids = [x.strip() for x in (ids or "").split(",") if x.strip()] or None
    sid = (session_id or "").strip()[:64] or None

    def _fetch() -> list[dict[str, Any]]:
        return authority.list_action_events(action_ids=action_ids, session_id=sid, since=since)

    return safe_event_poll(_fetch)


@router.get("/actions/{action_id}/status")
def get_action_status(action_id: str) -> dict[str, Any]:
    from aethos_core.runtime.actions import action_store

    action = action_store.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    events = authority.list_action_events(action_ids=[action_id])
    return {"action": action.to_dict(), "events": events}
