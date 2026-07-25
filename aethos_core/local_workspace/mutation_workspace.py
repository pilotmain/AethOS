# SPDX-License-Identifier: Apache-2.0
"""Local workspace mutation sandbox — isolated, auditable."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.agents.runtime.paths import agent_artifacts_root


def _sandbox_root() -> Path:
    return agent_artifacts_root() / "mutation_workspaces"


def create_mutation_workspace(
    *,
    repo_path: Path,
    branch_name: str | None = None,
    file_scope: list[str] | None = None,
) -> dict[str, Any]:
    """Create isolated sandbox copy — no writes to source repo."""
    workspace_id = f"mws-{uuid4().hex[:12]}"
    branch = branch_name or f"governed/aethos-{uuid4().hex[:8]}"
    root = _sandbox_root() / workspace_id
    root.mkdir(parents=True, exist_ok=True)
    sandbox_repo = root / "repo"
    if sandbox_repo.exists():
        shutil.rmtree(sandbox_repo)
    shutil.copytree(
        repo_path,
        sandbox_repo,
        ignore=shutil.ignore_patterns(".git", "node_modules", ".next", "__pycache__", ".venv", "venv"),
        dirs_exist_ok=True,
    )
    scoped = file_scope or []
    record = {
        "workspace_id": workspace_id,
        "branch": branch,
        "source_repo": str(repo_path),
        "sandbox_path": str(sandbox_repo),
        "files_modified": [],
        "file_scope": scoped,
        "diff_size": 0,
        "rollback_snapshot": None,
        "validation_status": "pending",
        "created_at": time(),
        "status": "isolated",
    }
    _save_record(workspace_id, record)
    return record


def stage_planned_patch(
    workspace: dict[str, Any],
    *,
    file_path: str,
    new_content: str,
) -> dict[str, Any]:
    """Stage a bounded patch in sandbox only."""
    sandbox = Path(workspace["sandbox_path"])
    target = sandbox / file_path
    if workspace.get("file_scope") and file_path not in workspace["file_scope"]:
        return {"ok": False, "error": "file_out_of_scope", "file": file_path}
    target.parent.mkdir(parents=True, exist_ok=True)
    old_size = target.stat().st_size if target.is_file() else 0
    target.write_text(new_content, encoding="utf-8")
    new_size = target.stat().st_size
    modified = list(workspace.get("files_modified") or [])
    if file_path not in modified:
        modified.append(file_path)
    workspace["files_modified"] = modified
    workspace["diff_size"] = int(workspace.get("diff_size") or 0) + abs(new_size - old_size)
    workspace["validation_status"] = "pending"
    _save_record(workspace["workspace_id"], workspace)
    return {"ok": True, "file": file_path, "diff_size": workspace["diff_size"]}


def get_mutation_workspace(workspace_id: str) -> dict[str, Any] | None:
    path = _sandbox_root() / workspace_id / "record.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_mutation_workspaces(*, limit: int = 20) -> list[dict[str, Any]]:
    root = _sandbox_root()
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for child in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        rec = get_mutation_workspace(child.name)
        if rec:
            rows.append(rec)
        if len(rows) >= limit:
            break
    return rows


def _save_record(workspace_id: str, record: dict[str, Any]) -> None:
    path = _sandbox_root() / workspace_id / "record.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
