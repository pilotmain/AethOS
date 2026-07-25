# SPDX-License-Identifier: Apache-2.0
"""Tenant egress policy — allow/deny with audit (§B8)."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_lock = threading.Lock()
_audit: list[dict[str, Any]] = []


def _store_path() -> Path:
    from aethos_core.config import get_settings

    raw = str(getattr(get_settings(), "net_policy_store_dir", "data/net_policy") or "data/net_policy")
    root = Path(raw)
    root.mkdir(parents=True, exist_ok=True)
    return root / "policy.json"


def _tenant_id() -> str:
    from aethos_core.tenancy.tenant_data_store import resolve_data_tenant

    return resolve_data_tenant()


def load_policy(tenant_id: str | None = None) -> dict[str, Any]:
    tid = (tenant_id or _tenant_id()).strip() or "default"
    path = _store_path()
    if not path.exists():
        return {"tenant_id": tid, "mode": "permissive", "allow": [], "deny": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return {
        "tenant_id": tid,
        "mode": str(data.get("mode") or "permissive"),
        "allow": list(data.get("allow") or []),
        "deny": list(data.get("deny") or []),
    }


def check_egress(url: str, *, tenant_id: str | None = None) -> tuple[bool, str]:
    """Return (allowed, reason)."""
    host = urlparse((url or "").strip()).hostname or ""
    if not host:
        return False, "invalid_url"
    policy = load_policy(tenant_id)
    deny = {str(h).lower() for h in policy.get("deny") or []}
    if host.lower() in deny:
        audit_egress(url=url, allowed=False, reason="deny_list", tenant_id=tenant_id)
        return False, "denied_by_policy"
    mode = str(policy.get("mode") or "permissive").lower()
    allow = {str(h).lower() for h in policy.get("allow") or []}
    if mode == "strict" and allow and host.lower() not in allow:
        audit_egress(url=url, allowed=False, reason="strict_allowlist", tenant_id=tenant_id)
        return False, "strict_mode_unknown_host"
    audit_egress(url=url, allowed=True, reason="ok", tenant_id=tenant_id)
    return True, "ok"


def audit_egress(
    *,
    url: str,
    allowed: bool,
    reason: str,
    tenant_id: str | None = None,
) -> None:
    with _lock:
        _audit.append(
            {
                "tenant_id": tenant_id or _tenant_id(),
                "url": url,
                "allowed": allowed,
                "reason": reason,
            }
        )


def list_egress_audit(limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        return list(_audit[-max(1, min(limit, 200)) :])
