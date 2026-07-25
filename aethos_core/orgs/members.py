# SPDX-License-Identifier: Apache-2.0
"""Organization members and role assignment."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.orgs.organizations import get_current_organization
from aethos_core.orgs.paths import orgs_root
from aethos_core.orgs.rbac import ROLES


def _path():
    return orgs_root() / "members.json"


def _load() -> dict[str, Any]:
    if not _path().is_file():
        default = _ensure_default_member()
        _save({"members": {default["member_id"]: default}})
        return _load()
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"members": {}}


def _save(data: dict[str, Any]) -> None:
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def _ensure_default_member() -> dict[str, Any]:
    # Use the legacy default org id directly — do not call get_current_organization()
    # here (it may call into members during multi-tenant bootstrap → recursion).
    return {
        "member_id": "member-default",
        "user_id": "default",
        "org_id": "org-default",
        "role": "admin",
        "created_at": time(),
    }


def find_member(*, user_id: str, org_id: str) -> dict[str, Any] | None:
    for m in (_load().get("members") or {}).values():
        if m.get("user_id") == user_id and m.get("org_id") == org_id:
            return m
    return None


def get_member_role(*, user_id: str = "default", org_id: str | None = None) -> str:
    oid = org_id or get_current_organization().get("org_id")
    m = find_member(user_id=user_id, org_id=oid)
    if m:
        role = str(m.get("role") or "viewer")
        return role if role in ROLES else "viewer"
    return "admin" if user_id == "default" else "viewer"


def assign_role(*, user_id: str, role: str, org_id: str | None = None) -> dict[str, Any]:
    if role not in ROLES:
        return {"ok": False, "error": "invalid_role"}
    oid = org_id or get_current_organization().get("org_id")
    member_id = f"member-{uuid4().hex[:8]}"
    record = {"member_id": member_id, "user_id": user_id, "org_id": oid, "role": role, "created_at": time()}
    data = _load()
    members = dict(data.get("members") or {})
    for mid, m in list(members.items()):
        if m.get("user_id") == user_id and m.get("org_id") == oid:
            del members[mid]
    members[member_id] = record
    data["members"] = members
    _save(data)
    return {"ok": True, "member": record}


def list_members(*, org_id: str | None = None) -> list[dict[str, Any]]:
    oid = org_id or get_current_organization().get("org_id")
    return [m for m in (_load().get("members") or {}).values() if m.get("org_id") == oid]
