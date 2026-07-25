# SPDX-License-Identifier: Apache-2.0
"""Continuous Monitor agents API — create/list/run stateful watchers.

Mounted under ``/api/v1``. Monitors are read-only watchers (perception); they never
mutate anything. Listing is scoped to the caller's tenant.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aethos_core.monitors import (
    create_monitor,
    delete_monitor,
    list_monitors,
    monitor_kinds,
    recent_observations,
    run_monitor,
    update_monitor,
)

router = APIRouter(tags=["monitors"])


class CreateMonitorIn(BaseModel):
    name: str
    kind: str
    target: str
    interval_sec: float = 300.0
    notify: str = "digest"
    enabled: bool = True


class UpdateMonitorIn(BaseModel):
    name: str | None = None
    target: str | None = None
    interval_sec: float | None = None
    notify: str | None = None
    enabled: bool | None = None


@router.get("/monitors")
def list_monitors_api() -> dict[str, Any]:
    return {"ok": True, "monitors": list_monitors(), "kinds": monitor_kinds()}


@router.get("/monitors/observations")
def recent_observations_api(limit: int = 20) -> dict[str, Any]:
    return {"ok": True, "observations": recent_observations(limit=min(max(limit, 1), 100))}


@router.post("/monitors")
def create_monitor_api(req: CreateMonitorIn) -> dict[str, Any]:
    try:
        rec = create_monitor(
            name=req.name,
            kind=req.kind,
            target=req.target,
            interval_sec=req.interval_sec,
            notify=req.notify,
            enabled=req.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "monitor": rec}


@router.post("/monitors/{monitor_id}/run")
def run_monitor_api(monitor_id: str) -> dict[str, Any]:
    result = run_monitor(monitor_id, force=True)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error", "monitor_not_found"))
    return result


@router.patch("/monitors/{monitor_id}")
def update_monitor_api(monitor_id: str, req: UpdateMonitorIn) -> dict[str, Any]:
    rec = update_monitor(monitor_id, **req.model_dump(exclude_none=True))
    if not rec:
        raise HTTPException(status_code=404, detail="monitor_not_found")
    return {"ok": True, "monitor": rec}


@router.delete("/monitors/{monitor_id}")
def delete_monitor_api(monitor_id: str) -> dict[str, Any]:
    if not delete_monitor(monitor_id):
        raise HTTPException(status_code=404, detail="monitor_not_found")
    return {"ok": True, "deleted": monitor_id}
