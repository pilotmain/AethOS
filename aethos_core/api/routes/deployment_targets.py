# SPDX-License-Identifier: Apache-2.0
"""Deployment target registry API — config-driven deploy profiles."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["deployment-targets"])


class RegisterDeploymentTargetIn(BaseModel):
    alias: str = Field(min_length=1, max_length=80)
    repo: str = Field(min_length=3, max_length=200)
    branch: str = Field(default="main", max_length=120)
    aliases: list[str] = Field(default_factory=list)
    workspace_id: str = Field(default="", max_length=80)
    local_path: str = Field(default="", max_length=512)
    vercel_project: str = Field(default="", max_length=120)
    railway_project: str = Field(default="", max_length=120)
    railway_service: str = Field(default="", max_length=120)
    railway_environment: str = Field(default="", max_length=80)
    root_directory: str = Field(default="", max_length=200)
    default_provider: str = Field(default="", max_length=40)
    confirm_production_binding: bool = False


def _looks_like_production_target(body: RegisterDeploymentTargetIn) -> bool:
    parts = [
        body.alias,
        body.railway_environment,
        body.railway_project,
        body.railway_service,
        body.vercel_project,
    ]
    joined = " ".join(str(p or "").lower() for p in parts)
    return any(token in joined for token in ("production", "prod"))


class UpdateDeploymentTargetIn(BaseModel):
    alias: str | None = Field(default=None, max_length=80)
    repo: str | None = Field(default=None, max_length=200)
    branch: str | None = Field(default=None, max_length=120)
    aliases: list[str] | None = None
    workspace_id: str | None = Field(default=None, max_length=80)
    local_path: str | None = Field(default=None, max_length=512)
    vercel_project: str | None = Field(default=None, max_length=120)
    railway_project: str | None = Field(default=None, max_length=120)
    railway_service: str | None = Field(default=None, max_length=120)
    railway_environment: str | None = Field(default=None, max_length=80)
    root_directory: str | None = Field(default=None, max_length=200)
    default_provider: str | None = Field(default=None, max_length=40)


class RegisterBindingIn(BaseModel):
    target_id: str = Field(min_length=1, max_length=80)
    session_id: str = Field(default="", max_length=120)
    user_id: str = Field(default="", max_length=120)
    channel: str = Field(default="", max_length=80)
    priority: int = Field(default=100, ge=0, le=1000)


class SetDefaultTargetIn(BaseModel):
    target_id: str = Field(min_length=1, max_length=80)


@router.get("/deployment-targets")
def list_deployment_targets_api() -> dict[str, Any]:
    from aethos_core.deployment_targets.bindings import get_default_target_id, list_bindings
    from aethos_core.deployment_targets.registry import list_targets

    return {
        "ok": True,
        "targets": list_targets(),
        "bindings": list_bindings(),
        "default_target_id": get_default_target_id(),
    }


@router.post("/deployment-targets/register")
def register_deployment_target_api(body: RegisterDeploymentTargetIn) -> dict[str, Any]:
    from aethos_core.deployment_targets.registry import register_target
    from aethos_core.governance.approval_privacy_governance import governance_diagnostics_snapshot

    if _looks_like_production_target(body) and not body.confirm_production_binding:
        diag = governance_diagnostics_snapshot()
        raise HTTPException(
            status_code=409,
            detail={
                "code": "production_binding_confirmation_required",
                "message": "Production deployment target binding requires confirm_production_binding=true.",
                "effective_mutation_flags": {
                    "mutation_execution_enabled": diag.get("mutation_execution_enabled"),
                    "production_mutations_unlocked": diag.get("aethos_solo_allow_production"),
                },
            },
        )

    try:
        record = register_target(
            alias=body.alias,
            repo=body.repo,
            branch=body.branch,
            aliases=body.aliases,
            workspace_id=body.workspace_id,
            local_path=body.local_path,
            vercel_project=body.vercel_project,
            railway_project=body.railway_project,
            railway_service=body.railway_service,
            railway_environment=body.railway_environment,
            root_directory=body.root_directory,
            default_provider=body.default_provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "target": record}


@router.get("/deployment-targets/resolve")
def resolve_deployment_target_api(
    text: str = "",
    session_id: str = "default",
    workspace_hint: str = "",
    user_id: str = "",
    channel: str = "web",
) -> dict[str, Any]:
    from aethos_core.deployment_targets.resolver import (
        format_deployment_target_resolution,
        resolve_deployment_target,
    )

    resolved = resolve_deployment_target(
        text,
        session_id=session_id,
        workspace_hint=workspace_hint,
        user_id=user_id,
        channel=channel,
    )
    return {
        "ok": bool(resolved.get("ok")),
        "resolution": resolved,
        "report": format_deployment_target_resolution(resolved),
    }


@router.get("/deployment-targets/{target_id}")
def get_deployment_target_api(target_id: str) -> dict[str, Any]:
    from aethos_core.deployment_targets.registry import get_target

    row = get_target(target_id)
    if not row:
        raise HTTPException(status_code=404, detail="Deployment target not found")
    return {"ok": True, "target": row}


@router.patch("/deployment-targets/{target_id}")
def update_deployment_target_api(target_id: str, body: UpdateDeploymentTargetIn) -> dict[str, Any]:
    from aethos_core.deployment_targets.registry import update_target

    patch = body.model_dump(exclude_none=True)
    if not patch:
        raise HTTPException(status_code=422, detail="No fields to update")
    try:
        updated = update_target(target_id, patch=patch)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=404, detail="Deployment target not found")
    return {"ok": True, "target": updated}


@router.delete("/deployment-targets/{target_id}")
def delete_deployment_target_api(target_id: str) -> dict[str, Any]:
    from aethos_core.deployment_targets.registry import delete_target

    if not delete_target(target_id):
        raise HTTPException(status_code=404, detail="Deployment target not found")
    return {"ok": True}


@router.post("/deployment-targets/bindings")
def register_binding_api(body: RegisterBindingIn) -> dict[str, Any]:
    from aethos_core.deployment_targets.bindings import register_binding

    try:
        record = register_binding(
            target_id=body.target_id,
            session_id=body.session_id,
            user_id=body.user_id,
            channel=body.channel,
            priority=body.priority,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "binding": record}


@router.post("/deployment-targets/default")
def set_default_target_api(body: SetDefaultTargetIn) -> dict[str, Any]:
    from aethos_core.deployment_targets.bindings import set_default_target
    from aethos_core.deployment_targets.registry import get_target

    if not get_target(body.target_id):
        raise HTTPException(status_code=404, detail="Deployment target not found")
    defaults = set_default_target(body.target_id)
    return {"ok": True, "defaults": defaults}


@router.delete("/deployment-targets/bindings/{binding_id}")
def delete_binding_api(binding_id: str) -> dict[str, Any]:
    from aethos_core.deployment_targets.bindings import delete_binding

    if not delete_binding(binding_id):
        raise HTTPException(status_code=404, detail="Binding not found")
    return {"ok": True}
