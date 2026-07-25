# SPDX-License-Identifier: Apache-2.0
"""Bridge auth users ↔ org members in multi-tenant mode (Phase 4).

Maps the request tenant (user email) to an isolated organization and syncs the
auth user's roles into the org RBAC vocabulary.
"""

from __future__ import annotations

import hashlib
from typing import Any

from aethos_core.orgs.rbac import ROLES
from aethos_core.tenancy import DEFAULT_TENANT


def org_id_for_tenant(tenant_id: str) -> str:
    """Stable org id for a tenant. Default tenant keeps the legacy org-default."""
    if tenant_id == DEFAULT_TENANT:
        return "org-default"
    digest = hashlib.sha256(tenant_id.encode("utf-8")).hexdigest()[:12]
    return f"org-{digest}"


def auth_roles_to_org_role(auth_roles: list[str] | tuple[str, ...] | None) -> str:
    """Map §2 auth roles → org RBAC roles."""
    roles = set(auth_roles or [])
    if "admin" in roles:
        return "admin"
    if "approver" in roles:
        return "reviewer"
    if "operator" in roles:
        return "operator"
    if "read_only" in roles:
        return "viewer"
    return "operator"


def ensure_tenant_org(
    tenant_id: str,
    *,
    display_name: str | None = None,
    auth_roles: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Get or create the org + member record for a tenant (multi-tenant mode)."""
    from aethos_core.orgs.members import assign_role, find_member
    from aethos_core.orgs.organizations import upsert_tenant_organization

    org_id = org_id_for_tenant(tenant_id)
    name = display_name or (tenant_id if "@" in tenant_id else f"Tenant {tenant_id[:8]}")
    org = upsert_tenant_organization(org_id=org_id, name=name, tenant_id=tenant_id)
    if find_member(user_id=tenant_id, org_id=org_id) is None:
        role = auth_roles_to_org_role(auth_roles)
        if role not in ROLES:
            role = "operator"
        assign_role(user_id=tenant_id, role=role, org_id=org_id)
    return org
