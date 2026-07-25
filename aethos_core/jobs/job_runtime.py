# SPDX-License-Identifier: Apache-2.0
"""Durable job runtime orchestration — Phase 11.7.9."""

from __future__ import annotations

from typing import Any

from aethos_core.jobs.job_governance import assess_job_governance
from aethos_core.jobs.job_memory import build_job_continuity
from aethos_core.jobs.job_registry import get_job_spec
from aethos_core.jobs.job_state import create_job_record, get_job, list_active_jobs, list_jobs, update_job
from aethos_core.jobs.trigger_adapter import dispatch_job, handle_trigger_callback


def create_governed_job(
    *,
    job_type: str,
    session_id: str = "default",
    entity_name: str | None = None,
    params: dict[str, Any] | None = None,
    auto_dispatch: bool = True,
) -> dict[str, Any]:
    governance = assess_job_governance(job_type=job_type, params=params)
    if not governance.get("allowed"):
        return {"ok": False, "reason": governance.get("reason"), "governance": governance}
    if governance.get("requires_approval"):
        job = create_job_record(
            job_type=job_type,
            session_id=session_id,
            entity_name=entity_name,
            params={**(params or {}), "approval_required": True},
        )
        update_job(job["job_id"], status="awaiting_approval")
        return {"ok": True, "job": job, "governance": governance, "requires_approval": True}

    spec = get_job_spec(job_type) or {}
    depends_on = spec.get("depends_on")
    if depends_on:
        prior = [j for j in list_jobs(session_id=session_id) if j.get("job_type") == depends_on and j.get("status") == "completed"]
        if not prior and auto_dispatch:
            create_governed_job(
                job_type=str(depends_on),
                session_id=session_id,
                entity_name=entity_name,
                params=params,
                auto_dispatch=True,
            )

    job = create_job_record(job_type=job_type, session_id=session_id, entity_name=entity_name, params=params)
    dispatch_result = None
    if auto_dispatch:
        dispatch_result = dispatch_job(job_id=job["job_id"])
    return {"ok": True, "job": job, "governance": governance, "dispatch": dispatch_result}


def enqueue_agent_workspace_jobs(*, session_id: str, agent_names: list[str]) -> dict[str, Any]:
    """Register durable background jobs for initialized agents (legacy bridge)."""
    from aethos_core.operational_entity_runtime.lightweight_agent_registry import get_workspace

    objective = str((get_workspace(session_id=session_id) or {}).get("objective") or "")
    created: list[dict[str, Any]] = []
    for name in agent_names:
        lower = name.lower()
        if any(token in lower for token in ("research", "analyst")) and not any(
            j.get("job_type") == "research_scan" for j in list_jobs(session_id=session_id)
        ):
            result = create_governed_job(
                job_type="research_scan",
                session_id=session_id,
                entity_name=name,
                params={"objective": objective} if objective else None,
            )
            if result.get("ok"):
                created.append(result["job"])
        if any(token in lower for token in ("strategist", "plan", "synthesis", "writer")) and not any(
            j.get("job_type") == "gtm_synthesis" for j in list_jobs(session_id=session_id)
        ):
            result = create_governed_job(
                job_type="gtm_synthesis",
                session_id=session_id,
                entity_name=name,
                params={"objective": objective} if objective else None,
            )
            if result.get("ok"):
                created.append(result["job"])
    return {"ok": bool(created), "jobs": created, "count": len(created)}


def cancel_governed_job(*, job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        return {"ok": False, "reason": "job_not_found"}
    if job.get("status") in {"completed", "failed", "cancelled"}:
        return {"ok": False, "reason": "terminal_state", "job": job}
    update_job(job_id, status="cancelled")
    return {"ok": True, "job": get_job(job_id)}


def get_durable_jobs_state(*, session_id: str = "default") -> dict[str, Any]:
    continuity = build_job_continuity(session_id=session_id)
    from aethos_core.config import get_settings

    s = get_settings()
    return {
        "ok": True,
        "phase": "11.7.9",
        "trigger_enabled": bool(getattr(s, "trigger_enabled", False)),
        "continuity": continuity,
        "active_jobs": list_active_jobs(session_id=session_id),
        "recent_jobs": list_jobs(session_id=session_id, limit=10),
    }


def process_trigger_callback(payload: dict[str, Any]) -> dict[str, Any]:
    job_id = str(payload.get("job_id") or "")
    status = str(payload.get("status") or "completed")
    output = dict(payload.get("output") or {})
    from aethos_core.external_execution_truth.webhook_security import validate_webhook_delivery

    validation = validate_webhook_delivery(
        job_id=job_id,
        payload=payload,
        signature=payload.get("signature"),
        delivery_id=payload.get("delivery_id"),
        sequence=payload.get("sequence"),
    )
    if not validation.get("ok"):
        return validation
    if validation.get("duplicate"):
        return {"ok": True, "duplicate": True, "reason": "idempotent_replay", "job_id": job_id}
    return handle_trigger_callback(job_id=job_id, status=status, output=output)
