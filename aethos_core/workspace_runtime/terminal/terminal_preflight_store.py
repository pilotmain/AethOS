# SPDX-License-Identifier: Apache-2.0
"""Terminal preflight store."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.workspace_runtime.paths import workspace_runtime_root


def _store_path():
    return workspace_runtime_root() / "terminal_preflights.json"


def _load() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {"preflights": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"preflights": {}}


def _save(data: dict[str, Any]) -> None:
    _store_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_terminal_preflight(preflight_id: str, record: dict[str, Any]) -> None:
    data = _load()
    preflights = dict(data.get("preflights") or {})
    preflights[preflight_id] = record
    data["preflights"] = preflights
    data["updated_at"] = time()
    _save(data)


def get_terminal_preflight(preflight_id: str) -> dict[str, Any] | None:
    return (_load().get("preflights") or {}).get(preflight_id)


def list_terminal_preflights(*, limit: int = 20) -> list[dict[str, Any]]:
    rows = list((_load().get("preflights") or {}).values())
    rows.sort(key=lambda r: float(r.get("created_at") or 0), reverse=True)
    return rows[:limit]


def approve_terminal_preflight(preflight_id: str) -> dict[str, Any]:
    row = get_terminal_preflight(preflight_id)
    if not row:
        return {"ok": False, "error": "not_found"}
    if row.get("status") == "policy_denied":
        return {"ok": False, "error": "policy_denied"}
    row["approved"] = True
    row["approval_status"] = "approved"
    row["approved_at"] = time()
    save_terminal_preflight(preflight_id, row)
    return {"ok": True, "preflight": row}


def clear_terminal_preflights_for_tests() -> None:
    path = _store_path()
    if path.is_file():
        path.unlink()
