# SPDX-License-Identifier: Apache-2.0
"""FIX 302 — identity and access hardening evaluation."""

from __future__ import annotations

from typing import Any

from aethos_core.orgs.rbac import can_perform, role_permissions


def role_has_tenant_permission(*, role: str, permission: str) -> bool:
    """Map FIX 300 tenant permissions to platform RBAC enforcement."""
    normalized = str(permission or "").strip().lower()
    perms = role_permissions(role)
    if normalized == "view":
        return "read" in perms
    if normalized == "review":
        return "read" in perms and "preflight_create" in perms
    if normalized == "approve":
        return can_perform(role=role, permission="approve_e2") or can_perform(
            role=role, permission="approve_e3"
        )
    if normalized == "operate":
        return "preflight_create" in perms and "watch_register" in perms
    if normalized == "administer":
        return "org_manage" in perms and "credential_manage" in perms
    if normalized == "govern":
        return can_perform(role=role, permission="approve_e3")
    return False


def evaluate_tenant_boundary(
    *,
    requester_org_id: str,
    target_org_id: str,
) -> dict[str, Any]:
    same_tenant = str(requester_org_id or "") == str(target_org_id or "")
    return {
        "allowed": same_tenant,
        "requester_org_id": requester_org_id,
        "target_org_id": target_org_id,
        "cross_tenant_access_enabled": False,
        "reason": None if same_tenant else "Cross-tenant access blocked by tenant boundary enforcement.",
    }


def evaluate_access_request(
    *,
    role: str,
    permission: str,
    requester_org_id: str,
    target_org_id: str | None = None,
) -> dict[str, Any]:
    boundary = evaluate_tenant_boundary(
        requester_org_id=requester_org_id,
        target_org_id=target_org_id or requester_org_id,
    )
    if not boundary["allowed"]:
        return {
            "allowed": False,
            "role": role,
            "permission": permission,
            "requester_org_id": requester_org_id,
            "target_org_id": target_org_id or requester_org_id,
            "tenant_boundary_passed": False,
            "permission_passed": False,
            "reason": boundary["reason"],
        }
    permission_passed = role_has_tenant_permission(role=role, permission=permission)
    return {
        "allowed": permission_passed,
        "role": role,
        "permission": permission,
        "requester_org_id": requester_org_id,
        "target_org_id": target_org_id or requester_org_id,
        "tenant_boundary_passed": True,
        "permission_passed": permission_passed,
        "reason": None
        if permission_passed
        else f"Role '{role}' lacks tenant permission '{permission}'.",
    }


def permission_matrix_for_roles(*, roles: tuple[str, ...]) -> list[dict[str, Any]]:
    from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_contract import (
        TENANT_PERMISSIONS,
    )

    rows: list[dict[str, Any]] = []
    for role in roles:
        rows.append(
            {
                "role": role,
                "permissions": {
                    perm: role_has_tenant_permission(role=role, permission=perm)
                    for perm in TENANT_PERMISSIONS
                },
            }
        )
    return rows
