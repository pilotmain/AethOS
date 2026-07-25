# SPDX-License-Identifier: Apache-2.0
"""Patch artifact storage."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.agents.runtime.paths import agent_artifacts_root


def _root() -> Path:
    return agent_artifacts_root() / "engineering_patches"


def new_patch_artifact_id() -> str:
    return f"epatch-{uuid4().hex[:12]}"


def store_patch_artifact(
    *,
    preflight_id: str,
    execution_id: str | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = new_patch_artifact_id()
    record = {
        "artifact_id": artifact_id,
        "preflight_id": preflight_id,
        "execution_id": execution_id,
        "created_at": time(),
        **payload,
    }
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{artifact_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _update_index(artifact_id)
    return record


def get_patch_artifact(artifact_id: str) -> dict[str, Any] | None:
    path = _root() / f"{artifact_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_patch_artifacts(*, limit: int = 20) -> list[dict[str, Any]]:
    index = _root() / "index.json"
    if not index.is_file():
        return []
    try:
        ids = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows: list[dict[str, Any]] = []
    for aid in ids[:limit]:
        row = get_patch_artifact(aid)
        if row:
            rows.append(row)
    return rows


def find_patch_artifact_for_preflight(preflight_id: str) -> dict[str, Any] | None:
    for row in list_patch_artifacts(limit=50):
        if row.get("preflight_id") == preflight_id:
            return row
    return None


def _update_index(artifact_id: str) -> None:
    index = _root() / "index.json"
    ids: list[str] = []
    if index.is_file():
        try:
            ids = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            ids = []
    ids.insert(0, artifact_id)
    index.write_text(json.dumps(ids[:200], indent=2), encoding="utf-8")


def clear_patch_artifacts_for_tests() -> None:
    root = _root()
    if root.is_dir():
        for p in root.glob("*.json"):
            p.unlink()
