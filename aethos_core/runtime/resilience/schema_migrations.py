# SPDX-License-Identifier: Apache-2.0
"""Schema migrations — safe runtime upgrades."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.production.paths import production_root

CURRENT_SCHEMA_VERSION = "9.9.0"

_MIGRATIONS: list[dict[str, Any]] = [
    {"version": "9.8.0", "description": "Baseline operational runtime"},
    {"version": "9.8K.0", "description": "Enterprise readiness artifacts"},
    {"version": "9.9.0", "description": "Production orgs, distributed queue, observability"},
]


def _state_path():
    return production_root() / "schema_version.json"


def get_schema_version() -> dict[str, Any]:
    path = _state_path()
    if not path.is_file():
        return {"version": "9.8.0", "migrated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": "9.8.0", "migrated_at": None}


def run_pending_migrations() -> dict[str, Any]:
    """Apply pending schema migrations."""
    current = get_schema_version()
    cur_ver = str(current.get("version") or "9.8.0")
    applied: list[str] = []
    for mig in _MIGRATIONS:
        if mig["version"] > cur_ver:
            _apply_migration(mig)
            applied.append(mig["version"])
            cur_ver = mig["version"]
    if applied:
        _state_path().write_text(
            json.dumps({"version": cur_ver, "migrated_at": time(), "applied": applied}, indent=2),
            encoding="utf-8",
        )
    return {"ok": True, "current_version": cur_ver, "target_version": CURRENT_SCHEMA_VERSION, "applied": applied}


def _apply_migration(migration: dict[str, Any]) -> None:
    production_root().mkdir(parents=True, exist_ok=True)
    (production_root() / f"migration_{migration['version']}.marker").write_text(migration["description"], encoding="utf-8")


def clear_migrations_for_tests() -> None:
    root = production_root()
    if root.is_dir():
        for p in root.glob("migration_*.marker"):
            p.unlink()
    path = _state_path()
    if path.is_file():
        path.unlink()
