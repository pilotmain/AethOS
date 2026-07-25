# SPDX-License-Identifier: Apache-2.0
"""Railway provider execution API — diagnostics, logs, evidence, diagnosis."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["railway-execution"])


class RailwayExecuteRequest(BaseModel):
    service_name: str
    job_id: str | None = None
    approved: bool = False


@router.get("/providers/railway/diagnostics")
def railway_diagnostics(
    service_name: str | None = None,
    service_id: str | None = None,
    project_name: str | None = None,
    environment: str = "production",
) -> dict[str, Any]:
    from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
    from aethos_core.providers.railway.restart_diagnostics import diagnose_railway_restart_target
    from aethos_core.providers.railway.target_resolver import ProviderTarget

    token, source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return {"ok": False, "detail": cred_error, "credential_source": source}
    target = ProviderTarget(
        provider="railway",
        service_name=service_name,
        service_id=service_id or None,
        project_name=project_name,
        environment=environment,
        resolved=bool(service_name or service_id),
        source="api",
    )
    diagnostics = diagnose_railway_restart_target(token, target=target, credential_source=source)
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "ok": diagnostics.ok,
        "diagnostics": diagnostics.to_dict(),
        "execution_mode": settings.railway_execution_mode,
        "credential_source": source,
    }


@router.get("/providers/railway/restart-diagnostics")
def railway_restart_diagnostics_alias(
    service_name: str | None = None,
    service_id: str | None = None,
    project_name: str | None = None,
    environment: str = "production",
) -> dict[str, Any]:
    return railway_diagnostics(
        service_name=service_name,
        service_id=service_id,
        project_name=project_name,
        environment=environment,
    )


@router.get("/providers/railway/logs")
def railway_logs(service_name: str, since: str | None = None, limit: int = 200) -> dict[str, Any]:
    from aethos_core.config import get_settings
    from aethos_core.providers.railway.cli_executor import railway_logs as cli_logs
    from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
    from aethos_core.providers.railway.api_client import fetch_deployment_logs, find_service_by_name, list_service_deployments

    settings = get_settings()
    mode = (settings.railway_execution_mode or "api").strip().lower()
    if mode == "cli":
        result = cli_logs(service_name=service_name, since=since, limit=limit)
        return {"ok": bool(result.get("ok")), "source": "cli", "logs": result.get("logs") or [], "command": result.get("command")}

    token, _, cred_error = resolve_railway_mutation_credentials()
    if not token:
        raise HTTPException(status_code=400, detail=cred_error or "Railway credentials not configured.")
    svc = find_service_by_name(token, service_name)
    if not svc:
        raise HTTPException(status_code=404, detail=f"Service `{service_name}` not found.")
    deployments = list_service_deployments(token, service_id=str(svc["service_id"]), limit=1)
    deployment_id = str(deployments[0].get("id") or "") if deployments else ""
    logs = fetch_deployment_logs(token, deployment_id=deployment_id) if deployment_id else []
    if since:
        logs = [row for row in logs if str(row.get("timestamp") or "") > since]
    return {"ok": True, "source": "api", "logs": logs[:limit], "deployment_id": deployment_id}


@router.get("/providers/railway/evidence/{job_id}")
def railway_evidence(job_id: str) -> dict[str, Any]:
    from aethos_core.provider_evidence.store import get_evidence_bundle

    result = get_evidence_bundle(job_id=job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=str(result.get("error") or "evidence_not_found"))
    return result


@router.post("/providers/railway/diagnose")
def railway_diagnose(body: dict[str, Any]) -> dict[str, Any]:
    job_id = str(body.get("job_id") or "")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id required")
    from aethos_core.provider_skills.runtime import diagnose_provider_job

    result = diagnose_provider_job(job_id=job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=str(result.get("error") or "diagnosis_failed"))
    return result


@router.post("/providers/railway/fix-plan")
def railway_fix_plan(body: dict[str, Any]) -> dict[str, Any]:
    job_id = str(body.get("job_id") or "")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id required")
    from aethos_core.provider_skills.runtime import fix_plan_for_job

    result = fix_plan_for_job(job_id=job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=str(result.get("error") or "fix_plan_failed"))
    return result


def _require_approved_job(job_id: str | None, approved: bool) -> None:
    if not approved:
        raise HTTPException(status_code=403, detail="Governed mutation requires approval before execution.")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id required for governed execution.")


@router.post("/providers/railway/execute/restart")
def railway_execute_restart(req: RailwayExecuteRequest) -> dict[str, Any]:
    _require_approved_job(req.job_id, req.approved)
    return _execute_via_skill(job_id=req.job_id, operation="restart", service_name=req.service_name, approved=True)


@router.post("/providers/railway/execute/redeploy")
def railway_execute_redeploy(req: RailwayExecuteRequest) -> dict[str, Any]:
    _require_approved_job(req.job_id, req.approved)
    return _execute_via_skill(job_id=req.job_id, operation="redeploy", service_name=req.service_name, approved=True)


@router.post("/providers/railway/execute/deploy")
def railway_execute_deploy(req: RailwayExecuteRequest) -> dict[str, Any]:
    _require_approved_job(req.job_id, req.approved)
    return _execute_via_skill(job_id=req.job_id, operation="deploy", service_name=req.service_name, approved=True)


def _execute_via_skill(*, job_id: str | None, operation: str, service_name: str, approved: bool) -> dict[str, Any]:
    from aethos_core.provider_skills.runtime import execute_provider_operation
    from aethos_core.providers.railway.target_resolver import ProviderTarget
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(str(job_id)) if job_id else None
    target_payload = (job.params.get("target") if job else None) or {}
    target = ProviderTarget(
        provider="railway",
        service_name=service_name,
        service_id=target_payload.get("service_id") if isinstance(target_payload, dict) else None,
        project_name=target_payload.get("project_name") if isinstance(target_payload, dict) else None,
        environment=target_payload.get("environment") if isinstance(target_payload, dict) else "production",
        resolved=True,
    )
    return execute_provider_operation(
        provider="railway",
        operation=operation,
        target=target,
        approved=approved,
        job_id=str(job_id),
        before_snapshot=(job.params.get("railway_before_snapshot") if job else None),
        approved_at=(job.params.get("mutation_execution_approved_at_iso") if job else None),
        request_id=str(job_id),
    )
