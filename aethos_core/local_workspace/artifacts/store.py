# SPDX-License-Identifier: Apache-2.0
"""Governed local workspace artifact storage."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.local_workspace.paths import artifacts_root

ARTIFACT_TYPES = frozenset(
    {
        "local_repo_scan",
        "git_status_snapshot",
        "architecture_analysis",
        "dependency_audit",
        "test_failure_report",
        "workspace_registration",
        "workflow_analysis",
    }
)


def new_artifact_id() -> str:
    return f"lart-{uuid4().hex[:12]}"


def _index_path() -> Path:
    return artifacts_root() / "index.json"


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
    tmp.replace(path)


def store_workspace_artifact(
    *,
    artifact_type: str,
    workspace_id: str | None,
    repo_path: str,
    payload: dict[str, Any],
    summary: str = "",
) -> dict[str, Any]:
    if artifact_type not in ARTIFACT_TYPES:
        raise ValueError(f"Unknown artifact type: {artifact_type}")
    artifact_id = new_artifact_id()
    record: dict[str, Any] = {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "workspace_id": workspace_id,
        "repo_path": repo_path,
        "created_at": time(),
        "summary": summary[:500],
        "payload": payload,
        "read_only": True,
    }
    body_path = artifacts_root() / "records" / f"{artifact_id}.json"
    _atomic_write(body_path, record)
    index = _load_index()
    index.insert(0, {k: record[k] for k in ("artifact_id", "artifact_type", "workspace_id", "repo_path", "created_at", "summary")})
    _atomic_write(_index_path(), {"artifacts": index[:500]})
    return record


def list_workspace_artifacts(*, limit: int = 40) -> list[dict[str, Any]]:
    return _load_index()[:limit]


def get_workspace_artifact(artifact_id: str) -> dict[str, Any] | None:
    path = artifacts_root() / "records" / f"{artifact_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _load_index() -> list[dict[str, Any]]:
    path = _index_path()
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw.get("artifacts") if isinstance(raw, dict) else raw
        return list(rows) if isinstance(rows, list) else []
    except (OSError, json.JSONDecodeError):
        return []
