# SPDX-License-Identifier: Apache-2.0
"""Railway provider discovery API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(tags=["railway-discovery"])


class RailwayDiagnoseBody(BaseModel):
    service_id: str | None = None
    service_name: str | None = None
    project_name: str | None = None
    environment: str | None = None


class RailwayPreflightBody(BaseModel):
    operation: str = Field(..., description="restart | redeploy | deploy")
    service_id: str | None = None
    service_name: str | None = None
    project_name: str | None = None
    environment: str | None = None
    user_request: str = ""


class RailwayExecuteBody(BaseModel):
    job_id: str
    approved: bool = True
    operation: str = "restart"


@router.get("/providers/railway/inventory")
def get_railway_inventory() -> dict[str, Any]:
    from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory

    inventory = get_provider_inventory(provider="railway")
    return {"ok": not inventory.error, "inventory": inventory.to_dict(), "error": inventory.error}


@router.post("/providers/railway/inventory/refresh")
def refresh_railway_inventory_route() -> dict[str, Any]:
    from aethos_core.provider_discovery.discovery_runtime import refresh_provider_inventory_runtime

    return refresh_provider_inventory_runtime(provider="railway")


@router.get("/providers/railway/services")
def list_railway_services(
    project: str | None = Query(default=None),
    environment: str | None = Query(default=None),
) -> dict[str, Any]:
    from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory

    inventory = get_provider_inventory(provider="railway")
    services = inventory.all_services()
    if project:
        services = [row for row in services if str(row.get("project_name") or "").lower() == project.lower()]
    if environment:
        services = [row for row in services if str(row.get("environment") or "").lower() == environment.lower()]
    return {"ok": True, "services": services, "count": len(services)}


@router.get("/providers/railway/service/{service_id}")
def get_railway_service(service_id: str) -> dict[str, Any]:
    from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory

    inventory = get_provider_inventory(provider="railway")
    row = inventory.find_service_by_id(service_id)
    if not row:
        raise HTTPException(status_code=404, detail="Service not found in Railway inventory.")
    deployments = []
    from aethos_core.providers.railway.discovery import list_railway_deployments

    deployments = list_railway_deployments(service_id, row.get("environment_id"))
    return {"ok": True, "service": row, "deployments": deployments}


@router.post("/providers/railway/operations/preflight")
def railway_operations_preflight(body: RailwayPreflightBody) -> dict[str, Any]:
    from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory
    from aethos_core.provider_discovery.target_resolution import resolve_target_from_inventory

    inventory = get_provider_inventory(provider="railway")
    phrase = body.service_name or body.service_id or body.user_request
    resolution = resolve_target_from_inventory(
        inventory=inventory,
        user_request=body.user_request or f"Railway {phrase}",
        target_hints=[phrase] if phrase else None,
    )
    if not resolution.resolved:
        return {
            "ok": False,
            "blocked": True,
            "reason": resolution.reason,
            "candidates": resolution.candidates,
            "detail": "No mutation preflight created — target unresolved.",
        }
    return {
        "ok": True,
        "blocked": False,
        "target": resolution.to_provider_target_dict(),
        "operation": body.operation,
        "detail": "Target resolved — create governed preflight via chat or Mission Control approval flow.",
    }


@router.post("/providers/railway/operations/execute")
def railway_operations_execute(body: RailwayExecuteBody) -> dict[str, Any]:
    if not body.approved:
        raise HTTPException(status_code=400, detail="Approved execution required.")
    from aethos_core.provider_skills.runtime import execute_provider_operation
    from aethos_core.providers.railway.target_resolver import ProviderTarget
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(body.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    target_raw = job.params.get("target") or {}
    target = ProviderTarget(
        provider="railway",
        service_name=str(target_raw.get("service_name") or job.params.get("target_name") or ""),
        service_id=target_raw.get("service_id"),
        project_name=target_raw.get("project_name"),
        environment=target_raw.get("environment"),
        resolved=True,
    )
    return execute_provider_operation(
        provider="railway",
        operation=body.operation,
        target=target,
        approved=True,
        job_id=body.job_id,
        before_snapshot=job.params.get("railway_before_snapshot") if isinstance(job.params.get("railway_before_snapshot"), dict) else None,
        approved_at=str(job.params.get("mutation_execution_approved_at_iso") or "") or None,
        request_id=body.job_id,
    )
