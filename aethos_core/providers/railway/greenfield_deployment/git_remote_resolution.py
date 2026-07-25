# SPDX-License-Identifier: Apache-2.0
"""Phase 2 — git remote resolution from local workspace."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo

_GITHUB_HTTPS_RX = re.compile(r"github\.com[:/]+([^/\s]+)/([^/\s#?]+)", re.I)
_GITHUB_SSH_RX = re.compile(r"git@github\.com:([^/\s]+)/([^/\s#?]+)", re.I)


def normalize_github_repository_slug(value: str) -> str:
    """Return `owner/repo` from SSH, HTTPS, or slug input."""
    raw = (value or "").strip()
    if not raw:
        return ""
    match = _GITHUB_SSH_RX.search(raw) or _GITHUB_HTTPS_RX.search(raw)
    if match:
        owner = match.group(1).strip().lower()
        repo = match.group(2).strip().removesuffix(".git").lower()
        return f"{owner}/{repo}"
    if "/" in raw and "@" not in raw and "://" not in raw:
        owner, repo = raw.split("/", 1)
        return f"{owner.strip().lower()}/{repo.strip().removesuffix('.git').lower()}"
    return raw.lower().removesuffix(".git")


def resolve_git_remote_from_workspace(workspace_root: str | Path) -> dict[str, Any]:
    """Resolve origin remote — never raises."""
    root = Path(workspace_root)
    if not root.is_dir():
        return _blocked("GIT_REMOTE_MISSING", "Workspace path is not a directory.")

    origin = _git_remote_url(root, "origin")
    if not origin:
        origin = _first_git_remote_url(root)
    if not origin:
        return _blocked(
            "GIT_REMOTE_MISSING",
            "No git remote configured for this workspace.",
            safe_next_command="Configure a GitHub remote (`git remote add origin owner/repo`) or select repo manually.",
        )

    owner, repo = _parse_remote(origin)
    if not owner or not repo:
        return _blocked(
            "GIT_REMOTE_MISSING",
            f"Could not parse git remote URL `{origin[:80]}`.",
            remote_url=origin,
            safe_next_command="Use a GitHub HTTPS or SSH remote URL.",
        )

    branch = _current_branch(root) or "main"
    provider = "github" if "github" in origin.lower() else "git"
    slug = normalize_github_repository_slug(f"{owner}/{repo}")

    return {
        "ok": True,
        "blocker_code": "",
        "provider": provider,
        "owner": owner,
        "repo": repo,
        "repository": slug,
        "branch": branch,
        "remote_url": origin,
        "remote_name": "origin",
    }


def format_git_remote_resolution_report(remote: dict[str, Any]) -> str:
    if not remote.get("ok"):
        return (
            f"**Git remote missing** (`{remote.get('blocker_code')}`)\n\n"
            f"- Detail: {remote.get('detail')}\n\n"
            f"**Required action:** {remote.get('safe_next_command')}\n\n"
            "No mutation has been performed."
        )
    return "\n".join(
        [
            "**Git remote resolution**",
            "",
            f"- Provider: `{remote.get('provider')}`",
            f"- Repository: `{remote.get('repository')}`",
            f"- Branch: `{remote.get('branch')}`",
            f"- Remote: `{remote.get('remote_name')}` → `{remote.get('remote_url')}`",
        ]
    )


def _blocked(code: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "blocker_code": code,
        "detail": detail,
        "safe_next_command": extra.pop(
            "safe_next_command",
            "Configure GitHub remote or select repo manually.",
        ),
        **extra,
    }


def _git_remote_url(repo: Path, name: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "remote", "get-url", name],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if proc.returncode == 0:
            return (proc.stdout or "").strip() or None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _first_git_remote_url(repo: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "remote"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if proc.returncode != 0:
            return None
        names = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]
        for name in names:
            url = _git_remote_url(repo, name)
            if url:
                return url
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _current_branch(repo: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if proc.returncode == 0:
            return (proc.stdout or "").strip() or None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _parse_remote(url: str) -> tuple[str, str]:
    match = _GITHUB_SSH_RX.search(url) or _GITHUB_HTTPS_RX.search(url)
    if match:
        owner = match.group(1).strip()
        repo = match.group(2).strip().removesuffix(".git")
        return owner, repo
    parsed = parse_owner_repo(url)
    if parsed[0] and parsed[1] and "@" not in parsed[0]:
        return parsed
    return "", ""
