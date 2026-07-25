# SPDX-License-Identifier: Apache-2.0
"""Local workspace registry — known repos and metadata."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.local_workspace.paths import workspaces_index_path
from aethos_core.local_workspace.canonical_path import (
    canonicalize_workspace_path,
    validate_registration_path,
)
from aethos_core.runtime.workspace_diagnostics import resolve_workspace_root


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _git_remote_origin(repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if out.returncode == 0:
            return (out.stdout or "").strip() or None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _default_branch(repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if out.returncode == 0:
            return (out.stdout or "").strip() or None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def resolve_workspace_path(path_or_hint: str | None = None) -> Path:
    if path_or_hint:
        hint = path_or_hint.strip()
        if hint.lower() in ("aethos", "this", "thisrepo"):
            return canonicalize_workspace_path(resolve_workspace_root())
        expanded = Path(hint).expanduser()
        if expanded.is_dir():
            return canonicalize_workspace_path(expanded.resolve())
    return canonicalize_workspace_path(resolve_workspace_root())


def list_workspaces() -> list[dict[str, Any]]:
    path = workspaces_index_path()
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = raw.get("workspaces") if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        return []
    return [dict(r) for r in rows if isinstance(r, dict)]


def get_workspace(workspace_id: str) -> dict[str, Any] | None:
    for row in list_workspaces():
        if row.get("workspace_id") == workspace_id:
            return row
    return None


def register_workspace(*, path: str, name: str | None = None) -> dict[str, Any]:
    from aethos_core.local_workspace.scanner import scan_workspace_stack
    from aethos_core.production.deployment_mode import is_hosted_deployment

    if is_hosted_deployment():
        raise ValueError(
            "Local path registration is not available on the hosted deployment. "
            "Connect a GitHub repository under Mission Control → Repositories instead."
        )

    raw = Path(path.strip()).expanduser()
    validate_registration_path(raw)
    repo = resolve_workspace_path(path)
    if not repo.is_dir():
        raise ValueError(f"Workspace path does not exist: {repo}")
    if not (repo / ".git").exists() and not (repo / "pyproject.toml").exists() and not (repo / "package.json").exists():
        raise ValueError(f"Path does not look like a workspace: {repo}")

    stack = scan_workspace_stack(repo)
    record: dict[str, Any] = {
        "workspace_id": f"ws-{uuid4().hex[:12]}",
        "name": (name or repo.name).strip() or repo.name,
        "path": str(repo),
        "remote_origin": _git_remote_origin(repo),
        "default_branch": _default_branch(repo),
        "stack": stack,
        "registered_at": time(),
        "last_scan_at": time(),
        "health_state": "registered",
    }

    existing = list_workspaces()
    for i, row in enumerate(existing):
        if str(row.get("path")) == str(repo):
            record["workspace_id"] = str(row.get("workspace_id") or record["workspace_id"])
            record["registered_at"] = row.get("registered_at") or record["registered_at"]
            existing[i] = record
            _atomic_write(workspaces_index_path(), {"workspaces": existing})
            return record

    existing.append(record)
    _atomic_write(workspaces_index_path(), {"workspaces": existing})
    return record


def update_workspace_scan(workspace_id: str, *, patch: dict[str, Any]) -> dict[str, Any] | None:
    rows = list_workspaces()
    for i, row in enumerate(rows):
        if row.get("workspace_id") == workspace_id:
            updated = {**row, **patch, "last_scan_at": time()}
            rows[i] = updated
            _atomic_write(workspaces_index_path(), {"workspaces": rows})
            return updated
    return None


def find_workspace_by_hint(hint: str) -> dict[str, Any] | None:
    normalized = (hint or "").strip().lower().replace("_", "").replace("-", "")
    for row in list_workspaces():
        name = str(row.get("name") or "").lower().replace("_", "").replace("-", "")
        if name == normalized or normalized in name:
            return row
    repo = resolve_workspace_path(hint if hint else None)
    for row in list_workspaces():
        if str(row.get("path")) == str(repo):
            return row

    from aethos_core.local_workspace.portfolio import find_project_in_portfolio

    portfolio_row = find_project_in_portfolio(hint)
    if portfolio_row:
        return portfolio_row
    try:
        from aethos_core.remote_workspace.registry import find_github_workspace

        gh = find_github_workspace(hint)
        if gh:
            return gh
    except Exception:  # noqa: BLE001
        pass
    return None
