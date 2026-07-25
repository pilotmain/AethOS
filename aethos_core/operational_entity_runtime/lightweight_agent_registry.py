# SPDX-License-Identifier: Apache-2.0
"""Lightweight agent registry — active operational entity tracking."""

from __future__ import annotations

import json
import re
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4


def _root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation" / "operational_entities"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(session_id: str) -> Path:
    safe = re.sub(r"[^\w\-]", "_", session_id)[:120]
    return _root() / f"entities_{safe}.json"


def _load(session_id: str) -> dict[str, Any]:
    path = _path(session_id)
    if not path.is_file():
        return {"entities": [], "workspace": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"entities": [], "workspace": {}}


def _save(session_id: str, data: dict[str, Any]) -> None:
    data["updated_at"] = time()
    _path(session_id).write_text(json.dumps(data, indent=2), encoding="utf-8")


def register_operational_entity(
    *,
    session_id: str = "default",
    name: str,
    role: str,
    objective: str | None = None,
) -> dict[str, Any]:
    data = _load(session_id)
    entities: list[dict[str, Any]] = list(data.get("entities") or [])
    entity_id = f"entity-{uuid4().hex[:10]}"
    row = {
        "entity_id": entity_id,
        "name": name.strip(),
        "role": role.strip(),
        "objective": objective,
        "status": "initialized",
        "created_at": time(),
        "last_active_at": time(),
    }
    entities = [e for e in entities if e.get("name", "").lower() != name.lower()]
    entities.insert(0, row)
    data["entities"] = entities[:12]
    _save(session_id, data)
    return row


def list_active_entities(*, session_id: str = "default") -> list[dict[str, Any]]:
    return list(_load(session_id).get("entities") or [])


def get_entity_by_name(*, session_id: str, name: str) -> dict[str, Any] | None:
    needle = name.lower()
    for entity in list_active_entities(session_id=session_id):
        if needle in str(entity.get("name", "")).lower() or needle in str(entity.get("role", "")).lower():
            return entity
    return None


def update_workspace(
    *,
    session_id: str = "default",
    objective: str,
    plan_steps: list[str] | None = None,
    artifact_ref: str | None = None,
) -> dict[str, Any]:
    data = _load(session_id)
    workspace = {
        "objective": objective,
        "plan_steps": plan_steps or [],
        "artifact_ref": artifact_ref,
        "status": "active",
        "updated_at": time(),
    }
    data["workspace"] = workspace
    _save(session_id, data)
    return workspace


def get_workspace(*, session_id: str = "default") -> dict[str, Any]:
    return dict(_load(session_id).get("workspace") or {})


def clear_operational_entities_for_tests() -> None:
    for p in _root().glob("*.json"):
        p.unlink()
