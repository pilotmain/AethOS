# SPDX-License-Identifier: Apache-2.0
"""Local repository readonly tooling — delegates to local_workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.local_workspace.git.intelligence import git_status_snapshot
from aethos_core.local_workspace.registry import resolve_workspace_path


def resolve_repo_root(hint: str | None = None) -> Path | None:
    try:
        repo = resolve_workspace_path(hint)
        if (repo / ".git").exists() or (repo / "pyproject.toml").exists() or (repo / "package.json").exists():
            return repo
    except Exception:
        pass
    return None


def git_status_readonly(repo_root: Path) -> dict[str, Any]:
    return git_status_snapshot(repo_root)


def format_repo_status_report(repo_root: Path, payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        return f"Could not read git status for `{repo_root}`: {payload.get('error', 'unknown error')}"
    lines = [
        "# Local repo status (readonly)\n",
        f"**Path:** `{repo_root}`",
        f"**Branch:** {payload.get('branch') or 'unknown'}",
        f"**Modified:** {payload.get('modified_count', 0)} · **Untracked:** {payload.get('untracked_count', 0)}",
        "",
        "```",
        payload.get("status_short") or "(clean)",
        "```",
        "",
        "**Writes blocked:** commit · push · merge · branch delete",
    ]
    return "\n".join(lines)
