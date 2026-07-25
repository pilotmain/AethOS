# SPDX-License-Identifier: Apache-2.0
"""Autonomous execution plane API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["autonomous_execution"])


def _require_autonomous_execution_enabled() -> None:
    from aethos_core.governance.approval_privacy_governance import is_autonomous_execution_enabled

    if not is_autonomous_execution_enabled():
        raise HTTPException(
            status_code=503,
            detail="Autonomous execution is disabled. Set AUTONOMOUS_EXECUTION_ENABLED=true to enable.",
        )


class SubmitPlannedTaskIn(BaseModel):
    steps: list[dict[str, Any]] = Field(min_length=1)
    owner: str = Field(default="operator", max_length=120)


@router.get("/autonomous-execution/status")
def get_autonomous_execution_status() -> dict[str, Any]:
    _require_autonomous_execution_enabled()
    from aethos_core.autonomous_execution.plane_service import plane_status_snapshot

    return plane_status_snapshot()


@router.post("/autonomous-execution/dispatch")
def post_autonomous_execution_dispatch() -> dict[str, Any]:
    _require_autonomous_execution_enabled()
    from aethos_core.autonomous_execution.plane_service import dispatch_until_idle

    return dispatch_until_idle()


@router.post("/autonomous-execution/tasks/noop")
def post_autonomous_execution_noop_task() -> dict[str, Any]:
    _require_autonomous_execution_enabled()
    from aethos_core.autonomous_execution.plane_service import submit_noop_task

    return submit_noop_task()


@router.post("/autonomous-execution/tasks/planned")
def post_autonomous_execution_planned_task(body: SubmitPlannedTaskIn) -> dict[str, Any]:
    _require_autonomous_execution_enabled()
    from aethos_core.autonomous_execution.plane_service import submit_planned_task

    return submit_planned_task(steps=body.steps, owner=body.owner)
