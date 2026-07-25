# SPDX-License-Identifier: Apache-2.0
"""Organizations API — RBAC and tenant management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["organizations"])


class CreateOrgRequest(BaseModel):
    name: str
    plan: str = "team"


class AssignRoleRequest(BaseModel):
    user_id: str
    role: str


class RegisterWorkspaceRequest(BaseModel):
    name: str
    repo_hint: str = "aethos"


class RbacCheckRequest(BaseModel):
    user_id: str = "default"
    action: str
    engineering_tier: str | None = None


@router.get("/orgs/current")
def orgs_current_api() -> dict[str, Any]:
    from aethos_core.orgs.members import get_member_role, list_members
    from aethos_core.orgs.organizations import get_current_organization

    org = get_current_organization()
    return {"ok": True, "organization": org, "members": list_members(), "current_role": get_member_role()}


@router.get("/orgs")
def orgs_list_api() -> dict[str, Any]:
    from aethos_core.orgs.organizations import list_organizations

    return {"ok": True, "organizations": list_organizations()}


@router.post("/orgs")
def orgs_create_api(body: CreateOrgRequest) -> dict[str, Any]:
    from aethos_core.orgs.organizations import create_organization

    return {"ok": True, "organization": create_organization(name=body.name, plan=body.plan)}


@router.get("/orgs/workspaces")
def orgs_workspaces_api() -> dict[str, Any]:
    from aethos_core.orgs.workspaces import list_workspaces

    return {"ok": True, "workspaces": list_workspaces()}


@router.post("/orgs/workspaces")
def orgs_register_workspace_api(body: RegisterWorkspaceRequest) -> dict[str, Any]:
    from aethos_core.orgs.workspaces import register_workspace

    return {"ok": True, "workspace": register_workspace(name=body.name, repo_hint=body.repo_hint)}


@router.post("/orgs/members/role")
def orgs_assign_role_api(body: AssignRoleRequest) -> dict[str, Any]:
    from aethos_core.orgs.members import assign_role

    result = assign_role(user_id=body.user_id, role=body.role)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/orgs/rbac/check")
def orgs_rbac_check_api(body: RbacCheckRequest) -> dict[str, Any]:
    from aethos_core.orgs.members import get_member_role
    from aethos_core.orgs.rbac import check_rbac

    role = get_member_role(user_id=body.user_id)
    return check_rbac(role=role, action=body.action, engineering_tier=body.engineering_tier)


@router.get("/orgs/audit")
def orgs_audit_api(limit: int = 50) -> dict[str, Any]:
    from aethos_core.orgs.audit_attribution import list_attributions

    return {"ok": True, "attributions": list_attributions(limit=limit)}
