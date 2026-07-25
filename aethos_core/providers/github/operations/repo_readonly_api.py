# SPDX-License-Identifier: Apache-2.0
"""GitHub repository readonly operations — inspect repo, branch, commits, checks."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo, request_github
from aethos_core.providers.github.shared.workflow_resolution import resolve_repository


def _resolve_owner_repo(token: str, *, repository: str) -> tuple[str, str, str] | None:
    owner, repo = parse_owner_repo(repository)
    if owner and repo:
        return owner, repo, f"{owner}/{repo}"
    resolved = resolve_repository(token, repository=repository)
    if not resolved.get("ok"):
        return None
    return str(resolved["owner"]), str(resolved["repo"]), str(resolved["full_name"])


def inspect_repo(token: str, *, repository: str) -> dict[str, Any]:
    resolved = _resolve_owner_repo(token, repository=repository)
    if resolved is None:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved.", "repository": repository}
    owner, repo, full_name = resolved
    result = request_github(token, "GET", f"/repos/{owner}/{repo}")
    if not result.get("ok"):
        return {"ok": False, "error": str(result.get("error") or "GitHub repo inspect failed."), "repository": full_name}
    data = dict(result.get("data") or {})
    return {
        "ok": True,
        "repository": full_name,
        "default_branch": str(data.get("default_branch") or ""),
        "private": bool(data.get("private")),
        "html_url": str(data.get("html_url") or ""),
        "description": str(data.get("description") or ""),
        "pushed_at": str(data.get("pushed_at") or ""),
        "open_issues_count": data.get("open_issues_count"),
        "repo": data,
    }


def fetch_branch_status(token: str, *, repository: str, branch: str | None = None) -> dict[str, Any]:
    resolved = _resolve_owner_repo(token, repository=repository)
    if resolved is None:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved.", "repository": repository}
    owner, repo, full_name = resolved
    repo_meta = inspect_repo(token, repository=full_name)
    branch_name = (branch or "").strip() or str((repo_meta.get("default_branch") if repo_meta.get("ok") else "") or "main")
    result = request_github(token, "GET", f"/repos/{owner}/{repo}/branches/{branch_name}")
    if not result.get("ok"):
        return {
            "ok": False,
            "error": str(result.get("error") or "Branch status unavailable."),
            "repository": full_name,
            "branch": branch_name,
        }
    data = dict(result.get("data") or {})
    commit = dict(data.get("commit") or {})
    return {
        "ok": True,
        "repository": full_name,
        "branch": branch_name,
        "protected": bool(data.get("protected")),
        "sha": str((commit.get("sha") if isinstance(commit, dict) else "") or ""),
        "committed_at": str(((commit.get("commit") or {}).get("committer") or {}).get("date") or ""),
    }


def fetch_recent_commits(token: str, *, repository: str, limit: int = 10) -> dict[str, Any]:
    resolved = _resolve_owner_repo(token, repository=repository)
    if resolved is None:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved.", "commits": []}
    owner, repo, full_name = resolved
    result = request_github(token, "GET", f"/repos/{owner}/{repo}/commits", params={"per_page": max(1, min(limit, 30))})
    if not result.get("ok"):
        return {"ok": False, "error": str(result.get("error") or "Commit list unavailable."), "commits": []}
    raw = result.get("data")
    commits: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for item in raw[:limit]:
            if not isinstance(item, dict):
                continue
            commit = dict(item.get("commit") or {})
            author = dict(commit.get("author") or {})
            commits.append(
                {
                    "sha": str(item.get("sha") or "")[:12],
                    "message": str((commit.get("message") or "").splitlines()[0] if commit.get("message") else ""),
                    "author": str(author.get("name") or ""),
                    "date": str(author.get("date") or ""),
                }
            )
    return {"ok": True, "repository": full_name, "commits": commits}


def fetch_failed_checks(token: str, *, repository: str, ref: str | None = None) -> dict[str, Any]:
    resolved = _resolve_owner_repo(token, repository=repository)
    if resolved is None:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved.", "checks": []}
    owner, repo, full_name = resolved
    branch_status = fetch_branch_status(token, repository=full_name)
    check_ref = (ref or "").strip() or str(branch_status.get("sha") or "")
    if not check_ref:
        return {"ok": False, "error": "No git ref available for check lookup.", "checks": []}
    result = request_github(token, "GET", f"/repos/{owner}/{repo}/commits/{check_ref}/check-runs", params={"per_page": 30})
    if not result.get("ok"):
        return {"ok": False, "error": str(result.get("error") or "Check runs unavailable."), "checks": []}
    data = dict(result.get("data") or {})
    runs = list(data.get("check_runs") or [])
    failed = [
        {
            "name": str(item.get("name") or ""),
            "status": str(item.get("status") or ""),
            "conclusion": str(item.get("conclusion") or ""),
            "details_url": str(item.get("details_url") or ""),
        }
        for item in runs
        if isinstance(item, dict) and str(item.get("conclusion") or "").lower() in {"failure", "cancelled", "timed_out"}
    ]
    return {"ok": True, "repository": full_name, "ref": check_ref, "checks": failed, "failed_count": len(failed)}


def list_open_issues(token: str, *, repository: str, limit: int = 10) -> dict[str, Any]:
    """Readonly open issues list for self-improvement intake (Phase 9.7)."""
    resolved = _resolve_owner_repo(token, repository=repository)
    if resolved is None:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved.", "issues": []}
    owner, repo, full_name = resolved
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/issues",
        params={"state": "open", "per_page": max(1, min(limit, 30))},
    )
    if not result.get("ok"):
        return {"ok": False, "error": str(result.get("error") or "Issue list unavailable."), "issues": []}
    raw = result.get("data")
    issues: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for item in raw[:limit]:
            if not isinstance(item, dict):
                continue
            if item.get("pull_request"):
                continue
            issues.append(
                {
                    "number": item.get("number"),
                    "title": str(item.get("title") or ""),
                    "html_url": str(item.get("html_url") or ""),
                    "labels": [str(l.get("name") or "") for l in (item.get("labels") or []) if isinstance(l, dict)],
                }
            )
    return {"ok": True, "repository": full_name, "issues": issues, "count": len(issues)}


def list_open_pull_requests(token: str, *, repository: str, limit: int = 10) -> dict[str, Any]:
    """Readonly open pull-request list."""
    resolved = _resolve_owner_repo(token, repository=repository)
    if resolved is None:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved.", "pull_requests": []}
    owner, repo, full_name = resolved
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/pulls",
        params={"state": "open", "per_page": max(1, min(limit, 30))},
    )
    if not result.get("ok"):
        return {"ok": False, "error": str(result.get("error") or "Pull-request list unavailable."), "pull_requests": []}
    raw = result.get("data")
    prs: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for item in raw[:limit]:
            if not isinstance(item, dict):
                continue
            prs.append(
                {
                    "number": item.get("number"),
                    "title": str(item.get("title") or ""),
                    "html_url": str(item.get("html_url") or ""),
                    "branch": str((item.get("head") or {}).get("ref") or "") if isinstance(item.get("head"), dict) else "",
                    "draft": bool(item.get("draft")),
                }
            )
    return {"ok": True, "repository": full_name, "pull_requests": prs, "count": len(prs)}
