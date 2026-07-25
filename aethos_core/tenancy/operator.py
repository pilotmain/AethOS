# SPDX-License-Identifier: Apache-2.0
"""Deployment operator vs tenant user (Phase 4).

In multi-tenant mode every authenticated user has their own tenant (typically
their email). **Deployment operators** are users with the auth ``admin`` role —
they alone may change deployment-level governance (kill switches, dangerous
flags, operator diagnostics). Tenant ``operator`` role users operate *their*
tenant only; they are not deployment operators.

Single-tenant (``MULTI_TENANT_ENABLED`` off): unchanged — existing RBAC applies
and the synthetic local operator is trusted.
"""

from __future__ import annotations

from typing import Any

# API paths that expose or mutate deployment-level governance. In multi-tenant
# mode these require the auth ``admin`` role (``MANAGE_GOVERNANCE`` permission).
OPERATOR_ONLY_PATH_MARKERS: tuple[str, ...] = (
    "/governance/overrides",
    "/governance/diagnostics",
)


def operator_only_path(path: str) -> bool:
    return any(marker in path for marker in OPERATOR_ONLY_PATH_MARKERS)


def is_deployment_admin(user: dict[str, Any] | None) -> bool:
    """True when the auth user holds the deployment ``admin`` role."""
    if not user:
        return False
    return "admin" in (user.get("roles") or [])


def is_deployment_operator(user: dict[str, Any] | None) -> bool:
    """May read/write deployment-level governance controls.

    Multi-tenant: requires auth ``admin``. Single-tenant: trusted when auth is
  off; when auth is on, still requires ``admin`` for governance paths.
    """
    from aethos_core.config import get_settings

    s = get_settings()
    if not s.multi_tenant_enabled:
        if not s.auth_enabled:
            return True
        return is_deployment_admin(user)
    return is_deployment_admin(user)


def require_deployment_operator(user: dict[str, Any] | None) -> bool:
    """Return True if the caller may proceed; False ⇒ forbidden for governance."""
    return is_deployment_operator(user)
