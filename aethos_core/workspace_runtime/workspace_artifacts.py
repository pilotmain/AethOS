# SPDX-License-Identifier: Apache-2.0
"""Workspace artifacts — evidence storage."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.workspace_runtime.paths import workspace_artifacts_root


def store_workspace_runtime_artifact(
    *,
    artifact_type: str,
    payload: dict[str, Any],
    workspace_id: str | None = None,
    session_id: str | None = None,
    summary: str = "",
) -> dict[str, Any]:
    artifact_id = f"wart-{uuid4().hex[:12]}"
    record = {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "workspace_id": workspace_id,
        "session_id": session_id,
        "summary": summary[:240],
        "created_at": time(),
        "payload": payload,
        "readonly": True,
    }
    root = workspace_artifacts_root()
    path = root / f"{artifact_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _update_index(artifact_id)
    return record


def get_workspace_runtime_artifact(artifact_id: str) -> dict[str, Any] | None:
    path = workspace_artifacts_root() / f"{artifact_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_workspace_runtime_artifacts(*, limit: int = 40) -> list[dict[str, Any]]:
    index = workspace_artifacts_root() / "index.json"
    if not index.is_file():
        return []
    try:
        ids = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows: list[dict[str, Any]] = []
    for aid in ids[:limit]:
        row = get_workspace_runtime_artifact(str(aid))
        if row:
            rows.append(row)
    return rows


def _update_index(artifact_id: str) -> None:
    index = workspace_artifacts_root() / "index.json"
    ids: list[str] = []
    if index.is_file():
        try:
            ids = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            ids = []
    ids.insert(0, artifact_id)
    index.write_text(json.dumps(ids[:300], indent=2), encoding="utf-8")


def clear_workspace_runtime_artifacts_for_tests() -> None:
    root = workspace_artifacts_root()
    if root.is_dir():
        for p in root.glob("*.json"):
            p.unlink()
