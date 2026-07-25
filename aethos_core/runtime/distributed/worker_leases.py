# SPDX-License-Identifier: Apache-2.0
"""Runtime leases — avoid duplicate execution."""

from __future__ import annotations

import json
import threading
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.production.paths import production_root

_LEASE_TTL_SEC = 120.0
_lock = threading.Lock()


def _path():
    return production_root() / "leases.json"


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"leases": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"leases": {}}


def _save(data: dict[str, Any]) -> None:
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def acquire_lease(*, resource_key: str, worker_id: str | None = None) -> dict[str, Any]:
    """Acquire exclusive lease — returns ok=False if held by another worker."""
    wid = worker_id or f"worker-{uuid4().hex[:8]}"
    now = time()
    with _lock:
        data = _load()
        leases = dict(data.get("leases") or {})
        existing = leases.get(resource_key)
        if existing and float(existing.get("expires_at") or 0) > now and existing.get("worker_id") != wid:
            return {
                "ok": False,
                "held_by": existing.get("worker_id"),
                "expires_at": existing.get("expires_at"),
            }
        lease = {"worker_id": wid, "acquired_at": now, "expires_at": now + _LEASE_TTL_SEC}
        leases[resource_key] = lease
        data["leases"] = leases
        _save(data)
        return {"ok": True, "worker_id": wid, "lease": lease}


def release_lease(*, resource_key: str, worker_id: str) -> dict[str, Any]:
    with _lock:
        data = _load()
        leases = dict(data.get("leases") or {})
        existing = leases.get(resource_key)
        if existing and existing.get("worker_id") == worker_id:
            del leases[resource_key]
            data["leases"] = leases
            _save(data)
            return {"ok": True}
        return {"ok": False, "error": "lease_not_held"}


def list_active_leases() -> list[dict[str, Any]]:
    now = time()
    rows = []
    for key, lease in (_load().get("leases") or {}).items():
        if float(lease.get("expires_at") or 0) > now:
            rows.append({"resource_key": key, **lease})
    return rows


def clear_leases_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
