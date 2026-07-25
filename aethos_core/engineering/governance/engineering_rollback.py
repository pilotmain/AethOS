# SPDX-License-Identifier: Apache-2.0
"""Engineering rollback — snapshot and restore."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.agents.runtime.paths import agent_artifacts_root


def _rollback_root() -> Path:
    return agent_artifacts_root() / "engineering_rollback"


def create_rollback_snapshot(
    *,
    workspace_id: str,
    branch: str,
    files_modified: list[str],
    sandbox_path: str | None = None,
) -> dict[str, Any]:
    """Persist rollback metadata + optional sandbox copy."""
    snapshot_id = f"ers-{uuid4().hex[:12]}"
    root = _rollback_root() / snapshot_id
    root.mkdir(parents=True, exist_ok=True)
    meta = {
        "snapshot_id": snapshot_id,
        "workspace_id": workspace_id,
        "branch": branch,
        "files_modified": files_modified,
        "sandbox_path": sandbox_path,
        "created_at": time(),
    }
    (root / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if sandbox_path and Path(sandbox_path).is_dir():
        dest = root / "sandbox"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(sandbox_path, dest, dirs_exist_ok=True)
        meta["sandbox_backup"] = str(dest)
        (root / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def rollback_plan_for_execution(execution: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategy": "revert_branch_restore_snapshot",
        "snapshot_id": execution.get("rollback_snapshot"),
        "branch": execution.get("branch"),
        "steps": [
            "Discard sandbox working changes",
            "Delete temporary branch if created",
            "Restore files from rollback snapshot",
            "Re-run readonly validation",
        ],
    }


def get_rollback_snapshot(snapshot_id: str) -> dict[str, Any] | None:
    path = _rollback_root() / snapshot_id / "meta.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_rollback_snapshots(*, limit: int = 20) -> list[dict[str, Any]]:
    root = _rollback_root()
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for child in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        snap = get_rollback_snapshot(child.name)
        if snap:
            rows.append(snap)
        if len(rows) >= limit:
            break
    return rows


def clear_rollback_snapshots_for_tests() -> None:
    root = _rollback_root()
    if root.is_dir():
        shutil.rmtree(root)
