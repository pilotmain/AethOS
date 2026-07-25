# SPDX-License-Identifier: Apache-2.0
"""Verify GitHub repository installation/access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GitHubAccessResult:
    ok: bool
    repo: str
    installation_id: str | None = None
    message: str = ""
    accessible_repos: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "repo": self.repo,
            "installation_id": self.installation_id,
            "message": self.message,
            "accessible_repos": list(self.accessible_repos or []),
        }


def list_accessible_github_repos() -> list[str] | None:
    try:
        from aethos_core.providers.github.auth import GitHubAuthAdapter
        from aethos_core.providers.github.api_client import list_repositories

        auth = GitHubAuthAdapter().resolve_best_auth_method(operation="read_repos")
        if not auth.get("credential_id"):
            return None
        token = GitHubAuthAdapter().get_api_token(str(auth["credential_id"]))
        listed = list_repositories(token)
        if not listed.get("ok"):
            return None
        repos = listed.get("repositories") or []
        return [str(r.get("full_name") or "") for r in repos if isinstance(r, dict) and r.get("full_name")]
    except Exception:
        return None


def verify_github_repo_access(
    full_name: str,
    *,
    accessible_repos: list[str] | None = None,
) -> GitHubAccessResult:
    repo = (full_name or "").strip()
    if not repo or "/" not in repo:
        return GitHubAccessResult(ok=False, repo=repo, message="Invalid repository name.")

    repos = accessible_repos if accessible_repos is not None else list_accessible_github_repos()
    if repos is None:
        return GitHubAccessResult(
            ok=False,
            repo=repo,
            message="GitHub credentials unavailable — cannot verify repository access.",
        )

    norm = repo.lower()
    matched = next((r for r in repos if r.lower() == norm), None)
    if matched:
        return GitHubAccessResult(
            ok=True,
            repo=matched,
            message=f"GitHub access verified for {matched}.",
            accessible_repos=repos,
        )

    return GitHubAccessResult(
        ok=False,
        repo=repo,
        message=f"No GitHub installation found for repo: {repo}",
        accessible_repos=repos,
    )
