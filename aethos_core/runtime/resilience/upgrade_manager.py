# SPDX-License-Identifier: Apache-2.0
"""Upgrade manager — runtime compatibility and rollback."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.production.paths import production_root
from aethos_core.runtime.resilience.schema_migrations import CURRENT_SCHEMA_VERSION, get_schema_version, run_pending_migrations


def check_upgrade_compatibility(*, target_version: str = CURRENT_SCHEMA_VERSION) -> dict[str, Any]:
    current = get_schema_version()
    cur = str(current.get("version") or "9.8.0")
    compatible = cur <= target_version
    return {
        "ok": compatible,
        "current_version": cur,
        "target_version": target_version,
        "upgrade_required": cur < target_version,
        "rollback_available": _rollback_snapshot_exists(),
    }


def run_upgrade() -> dict[str, Any]:
    """Run upgrade with pre-snapshot for rollback."""
    _save_rollback_snapshot()
    migrations = run_pending_migrations()
    return {
        "ok": True,
        "migrations": migrations,
        "rollback_snapshot_id": _latest_rollback_id(),
        "autonomous_execution_blocked": True,
    }


def rollback_upgrade() -> dict[str, Any]:
    """Rollback to pre-upgrade snapshot."""
    snap = _load_latest_rollback()
    if not snap:
        return {"ok": False, "error": "no_rollback_snapshot"}
    from aethos_core.runtime.resilience.schema_migrations import _state_path

    restored = {k: v for k, v in snap.items() if k != "rollback_id"}
    _state_path().write_text(json.dumps(restored, indent=2), encoding="utf-8")
    return {"ok": True, "restored_version": restored.get("version"), "rolled_back_at": time()}


def _rollback_dir():
    d = production_root() / "rollback"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_rollback_snapshot() -> None:
    snap = get_schema_version()
    rid = f"rb-{int(time())}"
    path = _rollback_dir() / f"{rid}.json"
    path.write_text(json.dumps({**snap, "rollback_id": rid}, indent=2), encoding="utf-8")


def _rollback_snapshot_exists() -> bool:
    return any(_rollback_dir().glob("rb-*.json"))


def _latest_rollback_id() -> str | None:
    files = sorted(_rollback_dir().glob("rb-*.json"), reverse=True)
    return files[0].stem if files else None


def _load_latest_rollback() -> dict[str, Any] | None:
    files = sorted(_rollback_dir().glob("rb-*.json"), reverse=True)
    if not files:
        return None
    try:
        return json.loads(files[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
