# SPDX-License-Identifier: Apache-2.0
"""Execute governed proactive automations — chat turns and durable jobs."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.automation.delivery import deliver_automation_message
from aethos_core.automation.store import (
    get_scheduled_task,
    get_webhook_trigger_with_secret_hash,
    record_automation_run,
    update_scheduled_task,
    verify_webhook_secret,
)
from aethos_core.tenancy.tenant_context import tenant_scope


def automation_enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "proactive_automation_enabled", False))


def _compose_prompt(base: str, payload: dict[str, Any] | None) -> str:
    prompt = (base or "").strip()
    if not payload:
        return prompt
    import json

    snippet = json.dumps(payload, default=str)[:1200]
    return f"{prompt}\n\nWebhook payload:\n{snippet}" if prompt else snippet


def _run_action(
    *,
    action_kind: str,
    prompt: str,
    job_type: str | None,
    session_id: str,
    allow_mutation: bool,
    source: str,
    ref_id: str,
) -> dict[str, Any]:
    if action_kind == "governed_job":
        jt = (job_type or "").strip()
        if not jt:
            return {"ok": False, "reason": "missing_job_type"}
        from aethos_core.jobs.job_governance import assess_job_governance
        from aethos_core.jobs.job_runtime import create_governed_job

        governance = assess_job_governance(job_type=jt, params={"source": source, "ref_id": ref_id})
        if not governance.get("allowed"):
            return {"ok": False, "reason": governance.get("reason"), "governance": governance}
        if governance.get("requires_approval") and not allow_mutation:
            job_result = create_governed_job(
                job_type=jt,
                session_id=session_id,
                params={"prompt": prompt, "source": source, "ref_id": ref_id},
                auto_dispatch=False,
            )
            return {
                "ok": True,
                "mode": "governed_job",
                "requires_approval": True,
                "job": job_result.get("job"),
                "summary": f"Mutation job `{jt}` queued for approval.",
            }
        job_result = create_governed_job(
            job_type=jt,
            session_id=session_id,
            params={"prompt": prompt, "source": source, "ref_id": ref_id},
            auto_dispatch=True,
        )
        summary = f"Governed job `{jt}` dispatched."
        if job_result.get("requires_approval"):
            summary = f"Governed job `{jt}` awaiting approval."
        return {
            "ok": True,
            "mode": "governed_job",
            "requires_approval": bool(job_result.get("requires_approval")),
            "job": job_result.get("job"),
            "summary": summary,
        }

    from aethos_core.chat.service import resolve_chat_turn

    turn = resolve_chat_turn(
        prompt,
        session_id=session_id,
        channel="automation",
        surface="automation",
        apply_relational_layer=False,
    )
    reply = str(getattr(turn, "reply", "") or "")[:3500]
    meta = dict(getattr(turn, "meta", None) or {})
    requires_approval = bool(meta.get("preflight_id") or meta.get("approval_required"))
    return {
        "ok": True,
        "mode": "chat",
        "reply": reply,
        "requires_approval": requires_approval,
        "summary": reply[:500] or "Automation chat turn completed.",
        "meta": meta,
    }


def execute_scheduled_task(task_id: str, *, tenant_id: str | None = None, force: bool = False) -> dict[str, Any]:
    if not automation_enabled() and not force:
        return {"ok": False, "reason": "proactive_automation_disabled"}

    task = get_scheduled_task(task_id, tenant_id=tenant_id)
    if not task:
        return {"ok": False, "reason": "task_not_found"}
    if not task.get("enabled") and not force:
        return {"ok": False, "reason": "task_disabled"}

    tid = tenant_id or task.get("_tenant_id")
    session_id = str(task.get("session_id") or "web-default")
    prompt = _compose_prompt(str(task.get("prompt") or ""), None)

    with tenant_scope(tid or "default"):
        result = _run_action(
            action_kind=str(task.get("action_kind") or "chat"),
            prompt=prompt,
            job_type=task.get("job_type"),
            session_id=session_id,
            allow_mutation=False,
            source="scheduled_task",
            ref_id=task_id,
        )

    delivery = None
    if result.get("ok"):
        delivery = deliver_automation_message(
            session_id=session_id,
            channel=str(task.get("delivery_channel") or "web"),
            message=str(result.get("summary") or result.get("reply") or "Scheduled task completed."),
            title=str(task.get("name") or "Scheduled automation"),
        )

    update_scheduled_task(
        task_id,
        {"last_run_at": time(), "last_status": "ok" if result.get("ok") else "failed"},
        tenant_id=tid,
    )
    record_automation_run(
        kind="scheduled",
        ref_id=task_id,
        status="ok" if result.get("ok") else "failed",
        detail={"result": result, "delivery": delivery},
        tenant_id=tid,
    )
    return {"ok": result.get("ok", False), "task_id": task_id, "result": result, "delivery": delivery}


def execute_webhook_trigger(
    trigger_id: str,
    *,
    secret: str,
    payload: dict[str, Any] | None = None,
    tenant_id: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    if not automation_enabled() and not force:
        return {"ok": False, "reason": "proactive_automation_disabled"}

    from aethos_core.automation.store import get_webhook_trigger, resolve_webhook_tenant, update_webhook_trigger

    tid = tenant_id or resolve_webhook_tenant(trigger_id)
    if not tid:
        return {"ok": False, "reason": "trigger_not_found"}

    trigger = get_webhook_trigger_with_secret_hash(trigger_id, tenant_id=tid)
    if not trigger:
        return {"ok": False, "reason": "trigger_not_found"}
    if not trigger.get("enabled"):
        return {"ok": False, "reason": "trigger_disabled"}
    if not verify_webhook_secret(trigger, secret):
        return {"ok": False, "reason": "invalid_secret"}

    session_id = str(trigger.get("session_id") or "web-default")
    prompt = _compose_prompt(str(trigger.get("prompt") or ""), payload)
    allow_mutation = bool(trigger.get("allow_mutation"))

    with tenant_scope(tid):
        result = _run_action(
            action_kind=str(trigger.get("action_kind") or "chat"),
            prompt=prompt,
            job_type=trigger.get("job_type"),
            session_id=session_id,
            allow_mutation=allow_mutation,
            source="webhook_trigger",
            ref_id=trigger_id,
        )

    delivery = None
    if result.get("ok"):
        delivery = deliver_automation_message(
            session_id=session_id,
            channel=str(trigger.get("delivery_channel") or "web"),
            message=str(result.get("summary") or result.get("reply") or "Webhook trigger completed."),
            title=str(trigger.get("name") or "Webhook automation"),
        )

    update_webhook_trigger(
        trigger_id,
        {
            "last_fired_at": time(),
            "fire_count": int(trigger.get("fire_count") or 0) + 1,
        },
        tenant_id=tid,
    )

    record_automation_run(
        kind="webhook",
        ref_id=trigger_id,
        status="ok" if result.get("ok") else "failed",
        detail={"payload": payload, "result": result, "delivery": delivery},
        tenant_id=tid,
    )
    public = get_webhook_trigger(trigger_id, tenant_id=tid)
    return {
        "ok": result.get("ok", False),
        "trigger_id": trigger_id,
        "result": result,
        "delivery": delivery,
        "trigger": public,
    }
