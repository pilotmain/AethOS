# SPDX-License-Identifier: Apache-2.0
"""Engineering memory — persisted context without secrets."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.local_workspace.paths import engineering_memory_path


def _load() -> dict[str, Any]:
    path = engineering_memory_path()
    if not path.is_file():
        return {"events": [], "repos": {}, "updated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"events": [], "repos": {}, "updated_at": None}


def _save(data: dict[str, Any]) -> None:
    path = engineering_memory_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_engineering_event(
    *,
    event: str,
    workspace_id: str | None = None,
    repo_path: str | None = None,
    detail: str | None = None,
) -> None:
    data = _load()
    row = {
        "at": time(),
        "event": event,
        "workspace_id": workspace_id,
        "repo_path": repo_path,
        "detail": (detail or "")[:240],
    }
    events = list(data.get("events") or [])
    events.insert(0, row)
    data["events"] = events[:200]
    if repo_path:
        repos = dict(data.get("repos") or {})
        repos[str(repo_path)] = {**repos.get(str(repo_path), {}), "last_event": event, "last_seen_at": time(), "workspace_id": workspace_id}
        data["repos"] = repos
    data["updated_at"] = time()
    _save(data)


def hydrate_workspace_memory(workspace: dict[str, Any], scan: dict[str, Any]) -> None:
    """Persist operational understanding — layers, stack, scan timestamps."""
    repo_path = str(workspace.get("path") or "")
    if not repo_path:
        return
    data = _load()
    repos = dict(data.get("repos") or {})
    arch = scan.get("architecture") if isinstance(scan.get("architecture"), dict) else scan if scan.get("layers") else {}
    if scan.get("architecture"):
        arch = scan["architecture"]
    deps = scan.get("dependencies") if isinstance(scan.get("dependencies"), dict) else {}
    layers = [l.get("layer") for l in arch.get("layers") or [] if isinstance(l, dict)]
    semantic = [s.get("label") for s in arch.get("semantic_modules") or [] if isinstance(s, dict)]
    repos[repo_path] = {
        "workspace_id": workspace.get("workspace_id"),
        "name": workspace.get("name"),
        "last_event": "memory_hydrated",
        "last_seen_at": time(),
        "last_scan_at": time(),
        "stack_badges": (workspace.get("stack") or {}).get("badges") if isinstance(workspace.get("stack"), dict) else [],
        "architecture_summary": arch.get("summary"),
        "architecture_layers": layers[:12],
        "semantic_modules": semantic[:12],
        "dependency_severity": deps.get("severity"),
        "remote_origin": workspace.get("remote_origin"),
        "default_branch": workspace.get("default_branch"),
    }
    data["repos"] = repos
    data["updated_at"] = time()
    _save(data)
    record_engineering_event(
        event="memory_hydrated",
        workspace_id=str(workspace.get("workspace_id") or "") or None,
        repo_path=repo_path,
        detail=arch.get("summary") or str(workspace.get("name") or ""),
    )


def get_engineering_memory() -> dict[str, Any]:
    return _load()


def clear_engineering_memory_for_tests() -> None:
    path = engineering_memory_path()
    if path.is_file():
        path.unlink()
