# SPDX-License-Identifier: Apache-2.0
"""Provider topology source binding API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["provider-topology"])


class ParseRepoBody(BaseModel):
    text: str = Field(..., description="User text containing a GitHub repo reference")


class VerifyRepoBody(BaseModel):
    repo: str = Field(..., description="owner/repo full name")


class UpdateBindingBody(BaseModel):
    provider: str = "railway"
    project: str
    environment: str = "production"
    service_name: str
    github_repo: str
    session_id: str = "default"
    confirm: bool = False


@router.post("/provider-topology/source-binding/parse")
def parse_source_binding_reference(body: ParseRepoBody) -> dict[str, Any]:
    from aethos_core.provider_topology.repo_reference_parser import parse_repo_reference

    ref = parse_repo_reference(body.text)
    return {"ok": ref is not None, "repo_ref": ref.to_dict() if ref else None}


@router.post("/provider-topology/source-binding/verify")
def verify_source_binding_access(body: VerifyRepoBody) -> dict[str, Any]:
    from aethos_core.provider_topology.github_access_verifier import verify_github_repo_access

    result = verify_github_repo_access(body.repo)
    return {"ok": result.ok, **result.to_dict()}


@router.post("/provider-topology/source-binding/update")
def update_source_binding(body: UpdateBindingBody) -> dict[str, Any]:
    from aethos_core.provider_topology.binding_update_flow import apply_binding_update, confirm_pending_update, get_pending_correction

    if body.confirm:
        outcome = confirm_pending_update(session_id=body.session_id)
        return outcome
    outcome = apply_binding_update(
        provider=body.provider,
        project=body.project,
        environment=body.environment,
        service_name=body.service_name,
        github_repo=body.github_repo,
    )
    pending = get_pending_correction(session_id=body.session_id)
    if pending:
        from aethos_core.provider_topology.binding_update_flow import clear_pending_correction

        clear_pending_correction(session_id=body.session_id)
    return outcome


class ReconcileBindingBody(BaseModel):
    provider: str = "railway"
    project: str
    environment: str = "production"
    service_name: str
    old_repo: str = ""
    candidate_repo: str | None = None
    local_path: str | None = None
    session_id: str = "default"
    confirm: bool = False


@router.post("/provider-topology/source-binding/reconcile")
def reconcile_source_binding_route(body: ReconcileBindingBody) -> dict[str, Any]:
    from aethos_core.provider_topology.repo_reconciliation import refresh_binding_from_remote, reconcile_source_binding

    if body.confirm:
        result = refresh_binding_from_remote(
            provider=body.provider,
            project=body.project,
            environment=body.environment,
            service_name=body.service_name,
            local_path=body.local_path,
            confirm=True,
        )
    else:
        result = reconcile_source_binding(
            provider=body.provider,
            project=body.project,
            environment=body.environment,
            service_name=body.service_name,
            old_repo=body.old_repo,
            candidate_repo=body.candidate_repo,
            local_path=body.local_path,
            session_id=body.session_id,
        )
    return {"ok": True, **result.to_dict()}


@router.get("/provider-topology/bindings")
def list_source_bindings() -> dict[str, Any]:
    from aethos_core.provider_topology.topology_memory import load_all_bindings

    bindings = load_all_bindings()
    return {"ok": True, "bindings": {key: row.to_dict() for key, row in bindings.items()}}
