# SPDX-License-Identifier: Apache-2.0
"""Hosted GitHub workspace registry — tenant-scoped repo connections."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from aethos_core.local_workspace.registry import list_workspaces as list_local_workspaces
from aethos_core.remote_workspace.github_clone import ensure_github_workspace, parse_github_repository
from aethos_core.remote_workspace.paths import remote_workspace_cache_root


def _index_path() -> Path:
    root = remote_workspace_cache_root()
    return root / "github_workspaces.json"


def _load() -> dict[str, Any]:
    path = _index_path()
    if not path.is_file():
        return {"workspaces": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"workspaces": []}
    if not isinstance(data, dict):
        return {"workspaces": []}
    data.setdefault("workspaces", [])
    return data


def _save(data: dict[str, Any]) -> None:
    path = _index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def list_github_workspaces() -> list[dict[str, Any]]:
    from aethos_core.tenancy import get_current_tenant

    tenant = get_current_tenant()
    rows = [dict(r) for r in _load().get("workspaces") or [] if isinstance(r, dict)]
    return [r for r in rows if str(r.get("tenant_id") or "default") == tenant]


def register_github_workspace(
    repository: str,
    *,
    branch: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    from aethos_core.tenancy import get_current_tenant

    repo_key = parse_github_repository(repository)
    if not repo_key:
        raise ValueError("Repository must be owner/repo (e.g. pilotmain/AethOS).")

    cloned = ensure_github_workspace(repo_key, branch=branch)
    if not cloned.get("ok"):
        raise ValueError(str(cloned.get("detail") or cloned.get("error") or "clone_failed"))

    tenant = get_current_tenant()
    data = _load()
    rows: list[dict[str, Any]] = list(data.get("workspaces") or [])
    existing = next(
        (
            r
            for r in rows
            if str(r.get("tenant_id")) == tenant and str(r.get("repository")) == repo_key
        ),
        None,
    )
    workspace_id = str(existing.get("workspace_id") or f"gh-{uuid4().hex[:10]}")
    row = {
        "workspace_id": workspace_id,
        "tenant_id": tenant,
        "source": "github",
        "repository": repo_key,
        "name": (name or "").strip() or repo_key.split("/", 1)[-1],
        "path": cloned.get("path"),
        "branch": branch or cloned.get("branch") or "default",
        "updated_at": time.time(),
    }
    rows = [r for r in rows if str(r.get("workspace_id")) != workspace_id]
    rows.insert(0, row)
    data["workspaces"] = rows[:100]
    _save(data)
    return row


def github_workspace_paths() -> list[Path]:
    paths: list[Path] = []
    for row in list_github_workspaces():
        raw = str(row.get("path") or "").strip()
        if not raw:
            continue
        try:
            p = Path(raw).expanduser().resolve()
            if p.is_dir():
                paths.append(p)
        except OSError:
            continue
    return paths


def find_github_workspace(hint: str | None) -> dict[str, Any] | None:
    hint = (hint or "").strip().lower()
    if not hint:
        return list_github_workspaces()[0] if list_github_workspaces() else None
    for row in list_github_workspaces():
        repo = str(row.get("repository") or "").lower()
        name = str(row.get("name") or "").lower()
        wid = str(row.get("workspace_id") or "").lower()
        if hint in {repo, name, wid} or hint in repo:
            return row
    parsed = parse_github_repository(hint)
    if parsed:
        for row in list_github_workspaces():
            if str(row.get("repository") or "").lower() == parsed.lower():
                return row
    return None


def merged_workspace_list() -> list[dict[str, Any]]:
    """Local + GitHub workspaces for the current tenant."""
    rows = [dict(r) for r in list_local_workspaces()]
    for gh in list_github_workspaces():
        rows.append(
            {
                **gh,
                "label": f"GitHub: {gh.get('repository')}",
            }
        )
    return rows
