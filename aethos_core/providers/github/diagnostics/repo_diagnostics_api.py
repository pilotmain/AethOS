# SPDX-License-Identifier: Apache-2.0
"""Extended GitHub repo diagnostics — branch divergence, PRs, releases."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.api_client import request_github
from aethos_core.providers.github.operations.repo_readonly_api import (
    _resolve_owner_repo,
    inspect_repo,
)


def fetch_branch_divergence(
    token: str,
    *,
    repository: str,
    base: str | None = None,
    head: str | None = None,
) -> dict[str, Any]:
    resolved = _resolve_owner_repo(token, repository=repository)
    if resolved is None:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved."}
    owner, repo, full_name = resolved
    repo_meta = inspect_repo(token, repository=full_name)
    default_branch = str((repo_meta.get("default_branch") if repo_meta.get("ok") else "") or "main")
    base_ref = (base or "").strip() or default_branch
    head_ref = (head or "").strip() or default_branch

    result = request_github(token, "GET", f"/repos/{owner}/{repo}/compare/{base_ref}...{head_ref}")
    if not result.get("ok"):
        return {
            "ok": False,
            "repository": full_name,
            "base": base_ref,
            "head": head_ref,
            "error": str(result.get("error") or "Branch compare unavailable."),
        }
    data = dict(result.get("data") or {})
    return {
        "ok": True,
        "repository": full_name,
        "base": base_ref,
        "head": head_ref,
        "ahead_by": int(data.get("ahead_by") or 0),
        "behind_by": int(data.get("behind_by") or 0),
        "status": str(data.get("status") or ""),
        "total_commits": len(list(data.get("commits") or [])),
        "files_changed": len(list(data.get("files") or [])),
    }


def fetch_open_pull_requests(token: str, *, repository: str, limit: int = 10) -> dict[str, Any]:
    resolved = _resolve_owner_repo(token, repository=repository)
    if resolved is None:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved.", "pull_requests": []}
    owner, repo, full_name = resolved
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/pulls",
        params={"state": "open", "per_page": max(1, min(limit, 30)), "sort": "updated", "direction": "desc"},
    )
    if not result.get("ok"):
        return {"ok": False, "error": str(result.get("error") or "Pull requests unavailable."), "pull_requests": []}
    raw = result.get("data")
    pulls: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for item in raw[:limit]:
            if not isinstance(item, dict):
                continue
            pulls.append(
                {
                    "number": item.get("number"),
                    "title": str(item.get("title") or ""),
                    "state": str(item.get("state") or ""),
                    "head": str((item.get("head") or {}).get("ref") or ""),
                    "base": str((item.get("base") or {}).get("ref") or ""),
                    "draft": bool(item.get("draft")),
                    "mergeable_state": str(item.get("mergeable_state") or ""),
                    "updated_at": str(item.get("updated_at") or ""),
                    "html_url": str(item.get("html_url") or ""),
                }
            )
    return {"ok": True, "repository": full_name, "pull_requests": pulls, "open_count": len(pulls)}


def fetch_pull_request_status(token: str, *, repository: str, pr_number: int | None = None) -> dict[str, Any]:
    resolved = _resolve_owner_repo(token, repository=repository)
    if resolved is None:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved."}
    owner, repo, full_name = resolved
    number = pr_number
    if number is None:
        open_prs = fetch_open_pull_requests(token, repository=full_name, limit=1)
        if not open_prs.get("ok") or not open_prs.get("pull_requests"):
            return {"ok": True, "repository": full_name, "pull_request": None, "message": "No open pull requests."}
        number = int(open_prs["pull_requests"][0]["number"])

    result = request_github(token, "GET", f"/repos/{owner}/{repo}/pulls/{number}")
    if not result.get("ok"):
        return {"ok": False, "error": str(result.get("error") or "Pull request unavailable.")}
    data = dict(result.get("data") or {})
    return {
        "ok": True,
        "repository": full_name,
        "pull_request": {
            "number": data.get("number"),
            "title": str(data.get("title") or ""),
            "state": str(data.get("state") or ""),
            "merged": bool(data.get("merged")),
            "head": str((data.get("head") or {}).get("ref") or ""),
            "base": str((data.get("base") or {}).get("ref") or ""),
            "mergeable_state": str(data.get("mergeable_state") or ""),
            "commits": data.get("commits"),
            "changed_files": data.get("changed_files"),
            "html_url": str(data.get("html_url") or ""),
        },
    }


def fetch_releases_and_tags(token: str, *, repository: str, limit: int = 5) -> dict[str, Any]:
    resolved = _resolve_owner_repo(token, repository=repository)
    if resolved is None:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved."}
    owner, repo, full_name = resolved
    releases_result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/releases",
        params={"per_page": max(1, min(limit, 10))},
    )
    tags_result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/tags",
        params={"per_page": max(1, min(limit, 10))},
    )
    releases: list[dict[str, Any]] = []
    if releases_result.get("ok") and isinstance(releases_result.get("data"), list):
        for row in releases_result["data"][:limit]:
            if isinstance(row, dict):
                releases.append(
                    {
                        "name": str(row.get("name") or row.get("tag_name") or ""),
                        "tag_name": str(row.get("tag_name") or ""),
                        "draft": bool(row.get("draft")),
                        "prerelease": bool(row.get("prerelease")),
                        "published_at": str(row.get("published_at") or ""),
                    }
                )
    tags: list[dict[str, Any]] = []
    if tags_result.get("ok") and isinstance(tags_result.get("data"), list):
        for row in tags_result["data"][:limit]:
            if isinstance(row, dict):
                tags.append(
                    {
                        "name": str(row.get("name") or ""),
                        "sha": str((row.get("commit") or {}).get("sha") or "")[:12],
                    }
                )
    return {
        "ok": True,
        "repository": full_name,
        "releases": releases,
        "tags": tags,
        "latest_release": releases[0] if releases else None,
        "latest_tag": tags[0]["name"] if tags else None,
    }


def detect_pending_local_changes_note(*, ahead_by: int, behind_by: int) -> str:
    if ahead_by == 0 and behind_by == 0:
        return "Remote branch compare shows no divergence on the inspected refs. Local uncommitted changes still require `git status` in the workspace."
    parts: list[str] = []
    if ahead_by:
        parts.append(f"{ahead_by} commit(s) ahead")
    if behind_by:
        parts.append(f"{behind_by} commit(s) behind")
    return f"Remote divergence detected ({', '.join(parts)}). Local uncommitted changes still require workspace `git status` if not yet pushed."
