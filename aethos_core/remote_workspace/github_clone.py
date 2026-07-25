# SPDX-License-Identifier: Apache-2.0
"""Shallow read-only GitHub clones for hosted repo analysis."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from aethos_core.remote_workspace.paths import github_clone_dir

_REPO_RX = re.compile(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)$")


def parse_github_repository(text: str) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("https://github.com/"):
        raw = raw.split("github.com/", 1)[-1].strip("/")
    if raw.endswith(".git"):
        raw = raw[:-4]
    parts = raw.split("/")
    if len(parts) >= 2:
        candidate = f"{parts[0]}/{parts[1]}"
        if _REPO_RX.match(candidate):
            return candidate
    if _REPO_RX.match(raw):
        return raw
    return None


def _github_token() -> str | None:
    from aethos_core.credentials import get_provider_api_token

    token = get_provider_api_token("github", require_validated=False)
    return str(token).strip() if token else None


def shallow_clone_github_repo(
    repository: str,
    *,
    branch: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Clone owner/repo shallow into tenant cache; returns {ok, path, repository}."""
    repo_key = parse_github_repository(repository)
    if not repo_key:
        return {"ok": False, "error": "invalid_repository", "repository": repository}

    token = _github_token()
    if not token:
        return {
            "ok": False,
            "error": "github_token_not_configured",
            "hint": "Connect GitHub in Mission Control → Advanced settings → Credentials first.",
        }

    target = github_clone_dir(repo_key, tenant_id=tenant_id)
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    target.parent.mkdir(parents=True, exist_ok=True)

    clone_url = f"https://x-access-token:{token}@github.com/{repo_key}.git"
    cmd = ["git", "clone", "--depth", "1", "--single-branch"]
    if branch and branch.strip():
        cmd.extend(["--branch", branch.strip()])
    cmd.extend([clone_url, str(target)])

    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": "clone_failed", "detail": str(exc)}

    if out.returncode != 0:
        detail = (out.stderr or out.stdout or "git clone failed").strip()[:400]
        return {"ok": False, "error": "clone_failed", "detail": detail}

    if not (target / ".git").exists():
        return {"ok": False, "error": "clone_failed", "detail": "clone produced no repository"}

    return {
        "ok": True,
        "repository": repo_key,
        "path": str(target.resolve()),
        "branch": branch or "default",
        "source": "github",
    }


def ensure_github_workspace(
    repository: str,
    *,
    branch: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Return an existing clone or refresh it."""
    repo_key = parse_github_repository(repository)
    if not repo_key:
        return {"ok": False, "error": "invalid_repository"}
    path = github_clone_dir(repo_key, tenant_id=tenant_id)
    if path.is_dir() and (path / ".git").exists():
        return {
            "ok": True,
            "repository": repo_key,
            "path": str(path.resolve()),
            "source": "github",
            "cached": True,
        }
    return shallow_clone_github_repo(repo_key, branch=branch, tenant_id=tenant_id)
