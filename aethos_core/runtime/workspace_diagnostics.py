# SPDX-License-Identifier: Apache-2.0
"""Canonical workspace paths — detect split-brain API vs profile store."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from time import time
from typing import Any

_api_started_at: float | None = None


def mark_api_started() -> None:
    global _api_started_at
    _api_started_at = time()


def api_process_started_at() -> float | None:
    return _api_started_at


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_configured_workspace_root() -> Path:
    """Return configured workspace root without canonical mutation-sandbox rewriting."""
    from aethos_core.config import get_settings

    env = (os.environ.get("AETHOS_WORKSPACE_ROOT") or "").strip()
    if not env:
        env = (get_settings().aethos_workspace_root or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return repo_root()


def resolve_workspace_root() -> Path:
    from aethos_core.local_workspace.canonical_path import canonicalize_workspace_path

    return canonicalize_workspace_path(resolve_configured_workspace_root())


def _git_short_commit(root: Path) -> str | None:
    env = (os.environ.get("AETHOS_BUILD_COMMIT") or "").strip()
    if env:
        return env[:12]
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if out.returncode == 0:
            return out.stdout.strip() or None
    except Exception:
        pass
    return None


def get_workspace_diagnostics() -> dict[str, Any]:
    from aethos_core.runtime.browser_profile_store import profiles_root_path

    root = resolve_workspace_root()
    repo = repo_root()
    cwd = Path.cwd().resolve()
    profile_store = profiles_root_path()

    canonical = str(root)
    warning: str | None = None
    if repo != root and not str(repo).startswith(str(root)):
        warning = (
            "AethOS appears to be running from a non-canonical workspace path. "
            f"Repo root is {repo} but AETHOS_WORKSPACE_ROOT is {root}."
        )
    elif cwd != root and cwd != repo and not str(cwd).startswith(str(root)):
        warning = (
            "API process cwd differs from workspace root. "
            f"cwd={cwd} · workspace={root}"
        )

    return {
        "workspace_root": canonical,
        "repo_root": str(repo),
        "process_cwd": str(cwd),
        "runtime_python": sys.executable,
        "profile_store_path": str(profile_store),
        "build_commit": _git_short_commit(repo),
        "api_process_started_at": _api_started_at,
        "aethos_workspace_root_env": (os.environ.get("AETHOS_WORKSPACE_ROOT") or "").strip() or None,
        "workspace_warning": warning,
        "canonical_workspace_ok": warning is None,
    }
