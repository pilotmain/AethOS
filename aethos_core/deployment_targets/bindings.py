# SPDX-License-Identifier: Apache-2.0
"""Session and channel bindings to deployment targets."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.deployment_targets.paths import bindings_index_path
from aethos_core.deployment_targets.registry import get_target, target_to_resolution


def _atomic_write(path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _load_index() -> dict[str, Any]:
    path = bindings_index_path()
    if not path.is_file():
        return {"bindings": [], "defaults": {}, "updated_at": None}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"bindings": [], "defaults": {}, "updated_at": None}
    if not isinstance(raw, dict):
        return {"bindings": [], "defaults": {}, "updated_at": None}
    if not isinstance(raw.get("bindings"), list):
        raw["bindings"] = []
    if not isinstance(raw.get("defaults"), dict):
        raw["defaults"] = {}
    return raw


def list_bindings() -> list[dict[str, Any]]:
    rows = _load_index().get("bindings") or []
    return [dict(r) for r in rows if isinstance(r, dict)]


def get_default_target_id() -> str:
    defaults = _load_index().get("defaults") or {}
    return str(defaults.get("target_id") or "")


def set_default_target(target_id: str) -> dict[str, Any]:
    index = _load_index()
    index["defaults"] = {"target_id": (target_id or "").strip()}
    index["updated_at"] = time()
    _atomic_write(bindings_index_path(), index)
    return index["defaults"]


def register_binding(
    *,
    target_id: str,
    session_id: str = "",
    user_id: str = "",
    channel: str = "",
    priority: int = 100,
) -> dict[str, Any]:
    if not get_target(target_id):
        raise ValueError(f"Unknown deployment target: {target_id}")
    record = {
        "binding_id": f"bind-{uuid4().hex[:12]}",
        "target_id": target_id,
        "match": {
            "session_id": (session_id or "*").strip() or "*",
            "user_id": (user_id or "*").strip() or "*",
            "channel": (channel or "*").strip() or "*",
        },
        "priority": int(priority),
        "registered_at": time(),
    }
    index = _load_index()
    rows = list(index.get("bindings") or [])
    rows.append(record)
    index["bindings"] = rows
    index["updated_at"] = time()
    _atomic_write(bindings_index_path(), index)
    return record


def delete_binding(binding_id: str) -> bool:
    index = _load_index()
    rows = list(index.get("bindings") or [])
    kept = [r for r in rows if str(r.get("binding_id") or "") != binding_id]
    if len(kept) == len(rows):
        return False
    index["bindings"] = kept
    index["updated_at"] = time()
    _atomic_write(bindings_index_path(), index)
    return True


def _match_score(match: dict[str, Any], *, session_id: str, user_id: str, channel: str) -> int:
    score = 0
    pairs = (
        ("session_id", session_id),
        ("user_id", user_id),
        ("channel", channel),
    )
    for key, value in pairs:
        expected = str(match.get(key) or "*").strip() or "*"
        actual = (value or "").strip()
        if expected == "*":
            continue
        if expected != actual:
            return -1
        score += 10
    return score


def resolve_bound_target(
    *,
    session_id: str = "default",
    user_id: str = "",
    channel: str = "web",
) -> dict[str, Any] | None:
    candidates: list[tuple[int, int, dict[str, Any]]] = []
    for row in list_bindings():
        match = row.get("match") if isinstance(row.get("match"), dict) else {}
        score = _match_score(match, session_id=session_id, user_id=user_id, channel=channel)
        if score < 0:
            continue
        priority = int(row.get("priority") or 0)
        candidates.append((score + priority, priority, row))

    if candidates:
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        target_id = str(candidates[0][2].get("target_id") or "")
        target = get_target(target_id)
        if target:
            return target_to_resolution(target, source="binding")

    default_id = get_default_target_id()
    if default_id:
        target = get_target(default_id)
        if target:
            return target_to_resolution(target, source="default_target")
    return None
