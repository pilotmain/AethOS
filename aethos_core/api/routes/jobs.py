# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from aethos_core.api.event_poll import safe_event_poll
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import JOB_TYPES

router = APIRouter(tags=["jobs"])


class CreateJobIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    job_type: str = Field(min_length=1, max_length=64)
    source: str = Field(default="api", max_length=32)
    session_id: str = Field(default="default", max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)
    auto_run: bool = True


class ResolveTargetIn(BaseModel):
    service_name: str = Field(min_length=1, max_length=200)


@router.post("/jobs")
def post_create_job(body: CreateJobIn) -> dict[str, Any]:
    if body.job_type not in JOB_TYPES:
        raise HTTPException(status_code=422, detail=f"Unknown job_type: {body.job_type}")
    try:
        job = authority.create_job(
            title=body.title,
            job_type=body.job_type,
            params=body.params,
            source=body.source,
            session_id=body.session_id,
            auto_run=body.auto_run,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return job.to_dict()


@router.get("/jobs")
def list_jobs() -> dict[str, Any]:
    """Tracked work units grouped by status."""
    from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

    tenant = get_current_tenant()
    grouped = authority.list_jobs_grouped()
    flat = [item for items in grouped.values() for item in items]
    flat = [
        j
        for j in flat
        if str((j.get("params") or {}).get("tenant_id") or DEFAULT_TENANT) == tenant
    ]
    filtered_grouped: dict[str, list] = {k: [] for k in grouped}
    for status, items in grouped.items():
        filtered_grouped[status] = [
            j
            for j in items
            if str((j.get("params") or {}).get("tenant_id") or DEFAULT_TENANT) == tenant
        ]
    return {"jobs": flat, "grouped": filtered_grouped, "count": len(flat)}


@router.get("/jobs/events")
def get_job_events(
    ids: str | None = None,
    session_id: str | None = None,
    since: float = 0.0,
) -> dict[str, Any]:
    job_ids = [x.strip() for x in (ids or "").split(",") if x.strip()] or None
    sid = (session_id or "").strip()[:64] or None

    def _fetch() -> list[dict[str, Any]]:
        return authority.list_job_events(job_ids=job_ids, session_id=sid, since=since)

    return safe_event_poll(_fetch)


@router.get("/jobs/pending-approvals")
def get_pending_mutation_approvals_api(session_id: str | None = None) -> dict[str, Any]:
    from aethos_core.jobs.job_approval_guidance import list_pending_mutation_approvals
    from aethos_core.jobs.pending_job_approval_resolution import list_pending_operational_approvals

    sid = (session_id or "default").strip() or "default"
    if sid in {"operator", "default"}:
        pending = list_pending_mutation_approvals(session_id=None)
        operational_sid: str | None = None
    else:
        pending = list_pending_mutation_approvals(session_id=sid)
        operational_sid = sid
    operational = [
        {
            "job_id": row.job_id,
            "job_type": row.job_type,
            "provider": row.provider,
            "label": row.label,
            "approval_route": row.approval_route,
            "approval_surface": "mission_control",
            "approval_state": "pending_approval",
        }
        for row in list_pending_operational_approvals(session_id=operational_sid)
        if row.job_id not in {p.get("job_id") for p in pending}
    ]
    merged = pending + operational
    return {"ok": True, "pending_approvals": merged, "count": len(merged)}


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    from aethos_core.runtime.jobs import job_store

    job_store.reap_stale_running_jobs()
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    events = authority.list_job_events(job_ids=[job_id])
    return {"job": job.to_dict(), "events": events}


@router.post("/jobs/{job_id}/approve-mutation-execution")
def post_approve_mutation_execution(job_id: str) -> dict[str, Any]:
    from aethos_core.operations.mutations.mutation_execution_flow import MutationExecutionError

    try:
        return authority.approve_mutation_execution(job_id)
    except MutationExecutionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.post("/jobs/{job_id}/approve-provider-e2e-orchestration")
def post_approve_provider_e2e_orchestration(job_id: str) -> dict[str, Any]:
    from aethos_core.provider_e2e_orchestration.approval_gate import ProviderE2EApprovalError

    try:
        return authority.approve_provider_e2e_orchestration(job_id)
    except ProviderE2EApprovalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.post("/jobs/{job_id}/approve-railway-greenfield-preflight")
def post_approve_railway_greenfield_preflight(job_id: str, session_id: str | None = None) -> dict[str, Any]:
    from aethos_core.providers.railway.greenfield_deployment.greenfield_approval_gate import GreenfieldApprovalError

    try:
        return authority.approve_railway_greenfield_preflight(job_id, session_id=session_id)
    except GreenfieldApprovalError as exc:
        raise HTTPException(status_code=409, detail=exc.result.detail or str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.post("/jobs/{job_id}/approve-vercel-greenfield-preflight")
def post_approve_vercel_greenfield_preflight(job_id: str, session_id: str | None = None) -> dict[str, Any]:
    from aethos_core.providers.railway.greenfield_deployment.greenfield_approval_gate import GreenfieldApprovalError

    try:
        return authority.approve_vercel_greenfield_preflight(job_id, session_id=session_id)
    except GreenfieldApprovalError as exc:
        raise HTTPException(status_code=409, detail=exc.result.detail or str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.post("/jobs/{job_id}/approve-supabase-env-completion")
def post_approve_supabase_env_completion(job_id: str) -> dict[str, Any]:
    from aethos_core.provider_e2e_orchestration.env_completion.supabase_approval import (
        SupabaseEnvCompletionApprovalError,
    )

    try:
        return authority.approve_supabase_env_completion(job_id)
    except SupabaseEnvCompletionApprovalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.post("/jobs/{job_id}/resolve-target")
def post_resolve_job_target(job_id: str, body: ResolveTargetIn) -> dict[str, Any]:
    from aethos_core.jobs.target_resolution import resolve_target_on_job

    result = resolve_target_on_job(job_id=job_id, service_name=body.service_name.strip())
    if not result.get("ok"):
        raise HTTPException(status_code=409, detail=result.get("reason", "target_unresolved"))
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    return {"ok": True, "job": job.to_dict() if job else None, **result}


@router.post("/jobs/{job_id}/refresh-targets")
def post_refresh_job_targets(job_id: str, limit: int = 20) -> dict[str, Any]:
    from aethos_core.jobs.target_resolution import refresh_job_target_candidates

    result = refresh_job_target_candidates(job_id=job_id, limit=limit)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("reason", "job_not_found"))
    return result


@router.post("/jobs/{job_id}/approve-readonly-execution")
def post_approve_readonly_execution(job_id: str) -> dict[str, Any]:
    from aethos_core.operations.preflight_execution import PreflightExecutionError

    try:
        return authority.approve_preflight_readonly_execution(job_id)
    except PreflightExecutionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.post("/jobs/{job_id}/cancel")
def post_cancel_job(job_id: str) -> dict[str, Any]:
    try:
        job = authority.cancel_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return job.to_dict()


# --- Phase 11.7.9 — Durable agent jobs ---


class DurableJobCreateIn(BaseModel):
    job_type: str = Field(min_length=1, max_length=64)
    session_id: str = Field(default="default", max_length=120)
    entity_name: str | None = Field(default=None, max_length=120)
    params: dict[str, Any] = Field(default_factory=dict)
    auto_dispatch: bool = True


class TriggerCallbackIn(BaseModel):
    job_id: str
    status: str = "completed"
    output: dict[str, Any] = Field(default_factory=dict)


@router.get("/jobs/durable/state")
def get_durable_jobs_state_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.jobs.job_runtime import get_durable_jobs_state

    return get_durable_jobs_state(session_id=session_id)


@router.get("/jobs/durable/active")
def get_durable_active_jobs_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.jobs.job_state import list_active_jobs

    jobs = list_active_jobs(session_id=session_id)
    return {"ok": True, "jobs": jobs, "count": len(jobs)}


@router.get("/jobs/durable/artifacts")
def get_durable_job_artifacts_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.operational_artifacts.artifact_store import list_session_artifacts

    return {"ok": True, "artifacts": list_session_artifacts(session_id=session_id)}


@router.get("/jobs/durable/recovery-windows")
def get_recovery_window_jobs_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.jobs.job_state import list_jobs

    jobs = [j for j in list_jobs(session_id=session_id) if j.get("job_type") == "recovery_window_check"]
    return {"ok": True, "jobs": jobs}


@router.get("/jobs/{job_id}/approval")
def get_tracked_job_approval_api(job_id: str, session_id: str | None = None) -> dict[str, Any]:
    from aethos_core.jobs.job_approval_guidance import get_job_approval_guidance

    return get_job_approval_guidance(job_id, session_id=session_id).to_dict()


@router.get("/jobs/durable/{job_id}/approval")
def get_durable_job_approval_api(job_id: str, session_id: str | None = None) -> dict[str, Any]:
    from aethos_core.jobs.job_approval_guidance import get_job_approval_guidance

    return get_job_approval_guidance(job_id, session_id=session_id).to_dict()


@router.post("/jobs/durable/{job_id}/approve")
def post_approve_durable_job(job_id: str) -> dict[str, Any]:
    from aethos_core.jobs.job_state import get_job, update_job
    from aethos_core.jobs.trigger_adapter import dispatch_job

    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Durable job not found")
    if str(job.get("status") or "") != "awaiting_approval":
        raise HTTPException(status_code=409, detail="Job is not awaiting approval")
    params = dict(job.get("params") or {})
    params.pop("approval_required", None)
    update_job(job_id, status="queued", params=params)
    dispatch_result = dispatch_job(job_id=job_id)
    return {"ok": True, "job_id": job_id, "dispatch": dispatch_result}


@router.get("/jobs/durable/{job_id}")
def get_durable_job_api(job_id: str) -> dict[str, Any]:
    from aethos_core.jobs.job_state import get_job

    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Durable job not found")
    return {"ok": True, "job": job}


@router.post("/jobs/durable/create")
def post_create_durable_job(body: DurableJobCreateIn) -> dict[str, Any]:
    from aethos_core.jobs.job_runtime import create_governed_job

    result = create_governed_job(
        job_type=body.job_type,
        session_id=body.session_id,
        entity_name=body.entity_name,
        params=body.params,
        auto_dispatch=body.auto_dispatch,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result.get("reason", "job_rejected"))
    return result


@router.post("/jobs/durable/{job_id}/cancel")
def post_cancel_durable_job(job_id: str) -> dict[str, Any]:
    from aethos_core.jobs.job_runtime import cancel_governed_job

    result = cancel_governed_job(job_id=job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=409, detail=result.get("reason", "cancel_failed"))
    return result


@router.post("/jobs/callback/trigger")
def post_trigger_callback(body: TriggerCallbackIn) -> dict[str, Any]:
    from aethos_core.jobs.job_runtime import process_trigger_callback

    return process_trigger_callback(body.model_dump())
