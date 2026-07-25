# SPDX-License-Identifier: Apache-2.0
"""RBAC — role-based access control for enterprise organizations."""

from __future__ import annotations

from typing import Any

ROLES = frozenset({"admin", "operator", "reviewer", "viewer"})

_PERMISSIONS: dict[str, frozenset[str]] = {
    "viewer": frozenset({"read", "audit_read"}),
    "operator": frozenset({"read", "audit_read", "preflight_create", "watch_register"}),
    "reviewer": frozenset({"read", "audit_read", "preflight_create", "approve_e2", "watch_register"}),
    "admin": frozenset(
        {
            "read",
            "audit_read",
            "preflight_create",
            "approve_e2",
            "approve_e3",
            "org_manage",
            "credential_manage",
            "watch_register",
        }
    ),
}


def role_permissions(role: str) -> frozenset[str]:
    return _PERMISSIONS.get(role, _PERMISSIONS["viewer"])


def can_perform(*, role: str, permission: str, engineering_tier: str | None = None) -> bool:
    """Check if role may perform action — E3+ requires admin."""
    perms = role_permissions(role)
    if permission == "approve_e3" or (permission == "approve" and engineering_tier in ("E3_pr_creation", "E3")):
        return "approve_e3" in perms
    if permission.startswith("approve") and engineering_tier in ("E2_branch_diff", "E2"):
        return "approve_e2" in perms or "approve_e3" in perms
    return permission in perms


def check_rbac(
    *,
    role: str,
    action: str,
    engineering_tier: str | None = None,
) -> dict[str, Any]:
    allowed = can_perform(role=role, permission=action, engineering_tier=engineering_tier)
    return {
        "allowed": allowed,
        "role": role,
        "action": action,
        "engineering_tier": engineering_tier,
        "autonomous_execution_blocked": True,
        "reason": None if allowed else f"Role '{role}' cannot perform '{action}'",
    }
