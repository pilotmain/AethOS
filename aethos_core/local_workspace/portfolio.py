# SPDX-License-Identifier: Apache-2.0
"""Workspace portfolio — parent directory containing many local projects."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from time import time
from typing import Any

from aethos_core.local_workspace.canonical_path import path_should_be_skipped_for_scan, validate_registration_path
from aethos_core.local_workspace.paths import registry_root

_PORTFOLIO_FILE = "portfolio.json"
_DEFAULT_MAX_DEPTH = 4
_DEFAULT_MAX_PROJECTS = 100

_HOME_SKIP_DIRS = frozenset(
    {
        "Library",
        "Pictures",
        "Music",
        "Movies",
        "Public",
        "Applications",
        ".Trash",
        "Downloads",
    }
)

_PATH_RX = re.compile(r"(/[\w./~-]+|~[\w./~-]+)")
_LOOK_HERE_RX = re.compile(
    r"\b(?:look(?:\s+at|\s+in|\s+here)?|check|see|go\s+to|open|find(?:\s+it)?(?:\s+in|\s+at)?|"
    r"pick\s+up|use|under|inside|from)\s+(/[\w./~-]+|~[\w./~-]+|[A-Za-z][\w.-]{1,})",
    re.I,
)


def _portfolio_path() -> Path:
    return registry_root() / _PORTFOLIO_FILE


def _load() -> dict[str, Any]:
    path = _portfolio_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _save(data: dict[str, Any]) -> None:
    path = _portfolio_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _configured_portfolio_root_env() -> str:
    import os

    from aethos_core.config import get_settings

    env = (os.environ.get("AETHOS_PORTFOLIO_ROOT") or "").strip()
    if env:
        return env
    return (get_settings().aethos_portfolio_root or "").strip()


def get_portfolio_config() -> dict[str, Any]:
    data = _load()
    root = str(data.get("portfolio_root") or _configured_portfolio_root_env() or "").strip()
    discovered = data.get("discovered") if isinstance(data.get("discovered"), list) else []
    return {
        "portfolio_root": root,
        "max_scan_depth": int(data.get("max_scan_depth") or _DEFAULT_MAX_DEPTH),
        "max_projects": int(data.get("max_projects") or _DEFAULT_MAX_PROJECTS),
        "last_discovered_at": data.get("last_discovered_at"),
        "discovered_count": len(discovered),
        "discovered": [dict(row) for row in discovered if isinstance(row, dict)],
    }


def set_portfolio_root(path: str, *, max_scan_depth: int | None = None, max_projects: int | None = None) -> dict[str, Any]:
    raw = Path(path.strip()).expanduser()
    validate_registration_path(raw)
    resolved = raw.resolve()
    if not resolved.is_dir():
        raise ValueError(f"Portfolio root does not exist: {resolved}")

    data = _load()
    data["portfolio_root"] = str(resolved)
    if max_scan_depth is not None:
        data["max_scan_depth"] = max(1, min(int(max_scan_depth), 8))
    if max_projects is not None:
        data["max_projects"] = max(1, min(int(max_projects), 200))
    data["updated_at"] = time()
    _save(data)
    return get_portfolio_config()


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


def _is_git_repo(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def _project_record(repo: Path) -> dict[str, Any]:
    return {
        "name": repo.name,
        "path": str(repo.resolve()),
        "remote_origin": _git_remote_origin(repo),
        "default_branch": _default_branch(repo),
        "discovered_at": time(),
    }


def discover_projects(*, rescan: bool = True, auto_register: bool = False) -> dict[str, Any]:
    config = get_portfolio_config()
    root_raw = str(config.get("portfolio_root") or "").strip()
    if not root_raw:
        return {
            "ok": False,
            "blocker_code": "PORTFOLIO_ROOT_MISSING",
            "detail": "Set a portfolio root (e.g. ~/projects) in Mission Control → Code workspaces.",
            "projects": [],
        }

    root = Path(root_raw).expanduser().resolve()
    if not root.is_dir():
        return {
            "ok": False,
            "blocker_code": "PORTFOLIO_ROOT_INVALID",
            "detail": f"Portfolio root is not a directory: {root}",
            "projects": [],
        }

    max_depth = int(config.get("max_scan_depth") or _DEFAULT_MAX_DEPTH)
    max_projects = int(config.get("max_projects") or _DEFAULT_MAX_PROJECTS)
    projects: list[dict[str, Any]] = []

    def walk(current: Path, depth: int) -> None:
        if len(projects) >= max_projects:
            return
        if depth > max_depth:
            return
        if depth > 0 and path_should_be_skipped_for_scan(current):
            return
        if depth == 1 and current.name in _HOME_SKIP_DIRS:
            return
        if _is_git_repo(current):
            projects.append(_project_record(current))
            return
        if depth >= max_depth:
            return
        try:
            for child in sorted(current.iterdir()):
                if not child.is_dir() or child.name.startswith("."):
                    continue
                walk(child, depth + 1)
        except (OSError, PermissionError):
            return

    walk(root, 0)

    data = _load()
    data["discovered"] = projects
    data["last_discovered_at"] = time()
    _save(data)

    registered: list[dict[str, Any]] = []
    if auto_register:
        from aethos_core.local_workspace.registry import register_workspace

        for project in projects:
            try:
                registered.append(register_workspace(path=str(project["path"]), name=str(project["name"])))
            except ValueError:
                continue

    return {
        "ok": True,
        "portfolio_root": str(root),
        "project_count": len(projects),
        "projects": projects,
        "auto_registered": len(registered),
        "registered": registered,
    }


def resolve_git_repo_root(path: str | Path) -> Path | None:
    """Walk up from a path until a git repo root is found."""
    raw = Path(str(path)).expanduser()
    try:
        current = raw.resolve()
    except OSError:
        return None
    if current.is_file():
        current = current.parent
    for _ in range(16):
        if _is_git_repo(current):
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


def extract_filesystem_paths(text: str) -> list[str]:
    """Extract absolute or home-relative paths from chat text."""
    raw = (text or "").strip()
    if not raw:
        return []
    paths: list[str] = []
    seen: set[str] = set()
    for match in _PATH_RX.finditer(raw):
        token = match.group(1).strip().rstrip(".,;:")
        if token and token not in seen:
            seen.add(token)
            paths.append(token)
    for match in _LOOK_HERE_RX.finditer(raw):
        token = match.group(1).strip().rstrip(".,;:")
        if token.startswith(("/", "~")) and token not in seen:
            seen.add(token)
            paths.append(token)
    return paths


def find_project_in_portfolio(hint: str, *, text: str | None = None) -> dict[str, Any] | None:
    """Resolve a project by path, folder name, or chat reference under the portfolio root."""
    combined = " ".join(part for part in ((text or "").strip(), (hint or "").strip()) if part).strip()
    if not combined:
        return None

    for path_token in extract_filesystem_paths(combined):
        expanded = Path(path_token).expanduser()
        if expanded.exists():
            repo_root = resolve_git_repo_root(expanded)
            if repo_root:
                return _match_record(repo_root, source="portfolio_path")

    normalized_hint = (hint or combined).strip()
    if normalized_hint.startswith("/") or normalized_hint.startswith("~"):
        expanded = Path(normalized_hint).expanduser()
        if expanded.exists():
            repo_root = resolve_git_repo_root(expanded)
            if repo_root:
                return _match_record(repo_root, source="portfolio_path")

    config = get_portfolio_config()
    projects = config.get("discovered") or []
    if not projects and config.get("portfolio_root"):
        discovery = discover_projects(rescan=True, auto_register=False)
        projects = discovery.get("projects") or []

    needle = _normalize_name(normalized_hint)
    if not needle:
        return None

    word_tokens = {_normalize_name(token) for token in re.findall(r"[A-Za-z0-9][\w.-]+", combined)}
    for row in projects:
        name_norm = _normalize_name(str(row.get("name") or ""))
        if name_norm and name_norm in word_tokens:
            return {**row, "source": "portfolio_name", "workspace_id": _linked_workspace_id(row)}

    exact = [row for row in projects if _normalize_name(str(row.get("name") or "")) == needle]
    if len(exact) == 1:
        return {**exact[0], "source": "portfolio_name", "workspace_id": _linked_workspace_id(exact[0])}
    if len(exact) > 1:
        return {
            **exact[0],
            "source": "portfolio_name",
            "workspace_id": _linked_workspace_id(exact[0]),
            "ambiguous_matches": len(exact),
        }

    partial = [
        row
        for row in projects
        if needle in _normalize_name(str(row.get("name") or ""))
        or _normalize_name(str(row.get("name") or "")) in needle
    ]
    if len(partial) == 1:
        return {**partial[0], "source": "portfolio_name_partial", "workspace_id": _linked_workspace_id(partial[0])}

    for row in projects:
        remote = str(row.get("remote_origin") or "").lower()
        if needle and needle in remote:
            return {**row, "source": "portfolio_remote", "workspace_id": _linked_workspace_id(row)}

    portfolio_root = str(config.get("portfolio_root") or "").strip()
    if portfolio_root:
        candidate = Path(portfolio_root).expanduser() / normalized_hint
        if candidate.is_dir():
            repo_root = resolve_git_repo_root(candidate)
            if repo_root:
                return _match_record(repo_root, source="portfolio_child_path")

    return None


def resolve_repo_reference(text_or_hint: str, *, session_id: str = "default") -> dict[str, Any]:
    """Human-style repo resolution: registered workspace → portfolio → configured root."""
    from aethos_core.local_workspace.registry import find_workspace_by_hint, list_workspaces, resolve_workspace_path
    from aethos_core.local_workspace.session_context import get_active_workspace, resolve_workspace_by_cwd_prefix

    hint = (text_or_hint or "").strip()
    if hint:
        ws = find_workspace_by_hint(hint)
        if ws:
            source = "registered" if ws.get("workspace_id") else str(ws.get("source") or "registered")
            return {**ws, "source": source, "resolved_path": str(ws.get("path") or "")}

        portfolio_match = find_project_in_portfolio(hint, text=hint)
        if portfolio_match:
            return {
                "ok": True,
                "name": portfolio_match.get("name"),
                "path": portfolio_match.get("path"),
                "remote_origin": portfolio_match.get("remote_origin"),
                "default_branch": portfolio_match.get("default_branch"),
                "workspace_id": portfolio_match.get("workspace_id"),
                "source": portfolio_match.get("source"),
                "resolved_path": str(portfolio_match.get("path") or ""),
            }

    for path_token in extract_filesystem_paths(hint):
        repo_root = resolve_git_repo_root(path_token)
        if repo_root:
            record = _match_record(repo_root, source="chat_path")
            return {
                "ok": True,
                "name": record.get("name"),
                "path": record.get("path"),
                "remote_origin": record.get("remote_origin"),
                "default_branch": record.get("default_branch"),
                "workspace_id": record.get("workspace_id"),
                "source": "chat_path",
                "resolved_path": str(repo_root),
            }

    active = get_active_workspace(session_id)
    if active and active.get("path"):
        return {**active, "source": "session_active", "resolved_path": str(active.get("path") or "")}

    cwd_row = resolve_workspace_by_cwd_prefix()
    if cwd_row and cwd_row.get("path"):
        return {**cwd_row, "source": "cwd_prefix", "resolved_path": str(cwd_row.get("path") or "")}

    portfolio = find_project_in_portfolio(hint)
    if portfolio:
        return {
            "ok": True,
            "name": portfolio.get("name"),
            "path": portfolio.get("path"),
            "remote_origin": portfolio.get("remote_origin"),
            "default_branch": portfolio.get("default_branch"),
            "workspace_id": portfolio.get("workspace_id"),
            "source": portfolio.get("source"),
            "resolved_path": str(portfolio.get("path") or ""),
        }

    rows = list_workspaces()
    if len(rows) == 1 and rows[0].get("path"):
        return {**rows[0], "source": "sole_registered", "resolved_path": str(rows[0].get("path") or "")}

    resolved = resolve_workspace_path(hint or None)
    return {
        "ok": True,
        "name": resolved.name,
        "path": str(resolved),
        "source": "configured_root",
        "resolved_path": str(resolved),
    }


def _match_record(repo_root: Path, *, source: str) -> dict[str, Any]:
    record = _project_record(repo_root)
    record["source"] = source
    record["workspace_id"] = _linked_workspace_id(record)
    return record


def _linked_workspace_id(project: dict[str, Any]) -> str | None:
    from aethos_core.local_workspace.registry import list_workspaces

    path = str(project.get("path") or "")
    for row in list_workspaces():
        if str(row.get("path") or "") == path:
            return str(row.get("workspace_id") or "") or None
    return None


def _normalize_name(value: str) -> str:
    return (value or "").strip().lower().replace("_", "-").replace(" ", "-")
