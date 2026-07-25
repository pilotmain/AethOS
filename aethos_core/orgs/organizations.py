# SPDX-License-Identifier: Apache-2.0
"""Organizations — tenant boundaries."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.orgs.paths import orgs_root


def _store_path():
    return orgs_root() / "organizations.json"


def _load() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        default = _default_org()
        _save({"organizations": {default["org_id"]: default}, "current_org_id": default["org_id"]})
        return _load()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"organizations": {}, "current_org_id": None}


def _save(data: dict[str, Any]) -> None:
    _store_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def _default_org() -> dict[str, Any]:
    return {
        "org_id": "org-default",
        "name": "Default Organization",
        "created_at": time(),
        "plan": "team",
        "tenant_isolated": True,
    }


def get_organization_by_id(org_id: str) -> dict[str, Any] | None:
    orgs = (_load().get("organizations") or {})
    return orgs.get(org_id)


def upsert_tenant_organization(*, org_id: str, name: str, tenant_id: str) -> dict[str, Any]:
    """Create or return an org bound to a multi-tenant tenant id."""
    data = _load()
    orgs = dict(data.get("organizations") or {})
    existing = orgs.get(org_id)
    if existing:
        return existing
    org = {
        "org_id": org_id,
        "name": name,
        "created_at": time(),
        "plan": "team",
        "tenant_isolated": True,
        "tenant_id": tenant_id,
    }
    orgs[org_id] = org
    data["organizations"] = orgs
    _save(data)
    return org


def get_current_organization() -> dict[str, Any]:
    """Return the org for the current context.

    Multi-tenant: derived from the request tenant (not the global pointer).
    Single-tenant: legacy global ``current_org_id`` pointer (unchanged).
    """
    from aethos_core.config import get_settings

    if get_settings().multi_tenant_enabled:
        from aethos_core.orgs.tenant_bridge import ensure_tenant_org
        from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

        tenant = get_current_tenant()
        if tenant == DEFAULT_TENANT:
            data = _load()
            oid = data.get("current_org_id") or "org-default"
            orgs = data.get("organizations") or {}
            return orgs.get(oid) or _default_org()
        return ensure_tenant_org(tenant)

    data = _load()
    oid = data.get("current_org_id") or "org-default"
    orgs = data.get("organizations") or {}
    return orgs.get(oid) or _default_org()


def list_organizations(*, limit: int = 20) -> list[dict[str, Any]]:
    return list((_load().get("organizations") or {}).values())[:limit]


def create_organization(*, name: str, plan: str = "team") -> dict[str, Any]:
    org_id = f"org-{uuid4().hex[:10]}"
    org = {"org_id": org_id, "name": name, "created_at": time(), "plan": plan, "tenant_isolated": True}
    data = _load()
    orgs = dict(data.get("organizations") or {})
    orgs[org_id] = org
    data["organizations"] = orgs
    if not data.get("current_org_id"):
        data["current_org_id"] = org_id
    _save(data)
    return org


def clear_orgs_for_tests() -> None:
    path = _store_path()
    if path.is_file():
        path.unlink()
    ws = orgs_root() / "workspaces.json"
    if ws.is_file():
        ws.unlink()
    members = orgs_root() / "members.json"
    if members.is_file():
        members.unlink()
