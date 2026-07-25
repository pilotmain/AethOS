# SPDX-License-Identifier: Apache-2.0
"""Proactive automation API — scheduled tasks and webhook triggers."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["automation"])


def _require_automation_enabled() -> None:
    from aethos_core.automation.executor import automation_enabled

    if not automation_enabled():
        raise HTTPException(
            status_code=503,
            detail="Proactive automation is disabled. Set PROACTIVE_AUTOMATION_ENABLED=true.",
        )


class ScheduledTaskIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=1, max_length=4000)
    schedule_kind: str = "interval"
    cron_expression: str | None = None
    interval_sec: int = Field(default=3600, ge=60, le=86400 * 7)
    action_kind: str = "chat"
    job_type: str | None = None
    delivery_channel: str = "web"
    delivery_target: str = "default"
    enabled: bool = True


class WebhookTriggerIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=1, max_length=4000)
    action_kind: str = "chat"
    job_type: str | None = None
    delivery_channel: str = "web"
    delivery_target: str = "default"
    allow_mutation: bool = False
    enabled: bool = True


class WebhookFireIn(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


@router.get("/automation/status")
def get_automation_status() -> dict[str, Any]:
    from aethos_core.automation.executor import automation_enabled
    from aethos_core.automation.scheduler import scheduler_status
    from aethos_core.jobs.job_registry import list_durable_job_types

    return {
        "ok": True,
        "enabled": automation_enabled(),
        "scheduler": scheduler_status(),
        "job_types": list_durable_job_types(),
    }


@router.get("/automation/schedules")
def list_schedules_api() -> dict[str, Any]:
    _require_automation_enabled()
    from aethos_core.automation.store import list_scheduled_tasks

    return {"ok": True, "tasks": list_scheduled_tasks()}


@router.post("/automation/schedules")
def create_schedule_api(body: ScheduledTaskIn) -> dict[str, Any]:
    _require_automation_enabled()
    from aethos_core.automation.store import create_scheduled_task

    task = create_scheduled_task(**body.model_dump())
    return {"ok": True, "task": task}


@router.delete("/automation/schedules/{task_id}")
def delete_schedule_api(task_id: str) -> dict[str, Any]:
    _require_automation_enabled()
    from aethos_core.automation.store import delete_scheduled_task

    if not delete_scheduled_task(task_id):
        raise HTTPException(status_code=404, detail="task_not_found")
    return {"ok": True, "task_id": task_id}


@router.post("/automation/schedules/{task_id}/run")
def run_schedule_api(task_id: str) -> dict[str, Any]:
    _require_automation_enabled()
    from aethos_core.automation.executor import execute_scheduled_task

    result = execute_scheduled_task(task_id, force=True)
    if not result.get("ok") and result.get("reason") == "task_not_found":
        raise HTTPException(status_code=404, detail="task_not_found")
    return result


@router.get("/automation/webhooks")
def list_webhooks_api() -> dict[str, Any]:
    _require_automation_enabled()
    from aethos_core.automation.store import list_webhook_triggers

    return {"ok": True, "triggers": list_webhook_triggers()}


@router.post("/automation/webhooks")
def create_webhook_api(body: WebhookTriggerIn) -> dict[str, Any]:
    _require_automation_enabled()
    from aethos_core.automation.store import create_webhook_trigger

    trigger = create_webhook_trigger(**body.model_dump())
    return {"ok": True, "trigger": trigger}


@router.delete("/automation/webhooks/{trigger_id}")
def delete_webhook_api(trigger_id: str) -> dict[str, Any]:
    _require_automation_enabled()
    from aethos_core.automation.store import delete_webhook_trigger

    if not delete_webhook_trigger(trigger_id):
        raise HTTPException(status_code=404, detail="trigger_not_found")
    return {"ok": True, "trigger_id": trigger_id}


@router.post("/automation/webhooks/{trigger_id}")
def fire_webhook_api(
    trigger_id: str,
    body: WebhookFireIn,
    x_aethos_webhook_secret: str | None = Header(default=None, alias="X-AethOS-Webhook-Secret"),
) -> dict[str, Any]:
    from aethos_core.automation.executor import automation_enabled, execute_webhook_trigger

    if not automation_enabled():
        raise HTTPException(status_code=503, detail="proactive_automation_disabled")
    secret = (x_aethos_webhook_secret or "").strip()
    if not secret:
        raise HTTPException(status_code=401, detail="missing_webhook_secret")
    result = execute_webhook_trigger(trigger_id, secret=secret, payload=body.payload)
    if result.get("reason") == "trigger_not_found":
        raise HTTPException(status_code=404, detail="trigger_not_found")
    if result.get("reason") == "invalid_secret":
        raise HTTPException(status_code=401, detail="invalid_webhook_secret")
    if result.get("reason") == "trigger_disabled":
        raise HTTPException(status_code=409, detail="trigger_disabled")
    return result


@router.post("/automation/tick")
def tick_automation_api() -> dict[str, Any]:
    _require_automation_enabled()
    from aethos_core.automation.scheduler import run_due_scheduled_tasks

    return run_due_scheduled_tasks()
