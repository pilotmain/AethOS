# SPDX-License-Identifier: Apache-2.0
"""FIX 306 — customer administration console evaluator."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.customer_administration_console.customer_administration_console_contract import (
    ADMIN_ONLY_SURFACES,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_evaluator import (
    evaluate_access_request,
    evaluate_tenant_boundary,
    permission_matrix_for_roles,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_contract import (
    GOVERNANCE_ACTIONS,
    GOVERNANCE_ACTION_PERMISSION,
    PLATFORM_ROLES,
)
from aethos_core.orgs.rbac import role_permissions


def evaluate_administration_access(
    *,
    role: str,
    requester_org_id: str,
    target_org_id: str | None = None,
) -> dict[str, Any]:
    boundary = evaluate_tenant_boundary(
        requester_org_id=requester_org_id,
        target_org_id=target_org_id or requester_org_id,
    )
    admin_eval = evaluate_access_request(
        role=role,
        permission="administer",
        requester_org_id=requester_org_id,
        target_org_id=target_org_id or requester_org_id,
    )
    return {
        "allowed": boundary["allowed"] and admin_eval["allowed"],
        "role": role,
        "requester_org_id": requester_org_id,
        "target_org_id": target_org_id or requester_org_id,
        "tenant_boundary_passed": boundary["allowed"],
        "admin_permission_passed": admin_eval["allowed"],
        "cross_tenant_administration_enabled": False,
        "reason": boundary.get("reason") or admin_eval.get("reason"),
    }


def admin_surface_access(*, role: str, requester_org_id: str) -> dict[str, bool]:
    access = evaluate_administration_access(role=role, requester_org_id=requester_org_id)
    allowed = access["allowed"]
    surfaces = {}
    for surface in ADMIN_ONLY_SURFACES:
        surfaces[surface] = allowed
    surfaces["organization_administration_report"] = True
    surfaces["workspace_administration_report"] = evaluate_access_request(
        role=role,
        permission="view",
        requester_org_id=requester_org_id,
    )["allowed"]
    surfaces["project_administration_report"] = surfaces["workspace_administration_report"]
    surfaces["channel_administration_report"] = surfaces["workspace_administration_report"]
    surfaces["customer_administration_dashboard"] = allowed or surfaces["workspace_administration_report"]
    return surfaces


def role_administration_rows() -> list[dict[str, Any]]:
    rows = []
    matrix = permission_matrix_for_roles(roles=PLATFORM_ROLES)
    for row in matrix:
        role = str(row.get("role") or "")
        granted = sorted(role_permissions(role))
        findings = []
        if role == "viewer" and "org_manage" in granted:
            findings.append("viewer_with_org_manage_drift")
        if role == "viewer" and "approve_e2" in granted:
            findings.append("viewer_with_approve_e2_drift")
        if role == "admin" and len(granted) > 6:
            findings.append("admin_broad_permission_surface_review_recommended")
        rows.append(
            {
                "role": role,
                "permissions": row.get("permissions") or {},
                "platform_permissions": granted,
                "least_privilege_findings": findings,
                "read_only": True,
            }
        )
    return rows


def governance_administration_rows(*, role: str, org_id: str) -> list[dict[str, Any]]:
    rows = []
    for action in GOVERNANCE_ACTIONS:
        required = dict(GOVERNANCE_ACTION_PERMISSION).get(action, "govern")
        result = evaluate_access_request(
            role=role,
            permission=required,
            requester_org_id=org_id,
        )
        rows.append(
            {
                "action": action,
                "required_permission": required,
                "visibility_allowed": result["allowed"],
                "mutation_allowed": False,
                "read_only": True,
            }
        )
    return rows
