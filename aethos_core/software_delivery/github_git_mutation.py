# SPDX-License-Identifier: Apache-2.0
"""FIX 125H — bounded GitHub Git API mutations for software delivery."""

from __future__ import annotations

import base64
import os
from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo, request_github
from aethos_core.software_delivery.branch_push_contract import PROTECTED_DEFAULT_BRANCHES
from aethos_core.software_delivery.governed_workspace import workspace_file_path, workspace_tree_root


def _certification_mode() -> bool:
    return os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}


def assert_feature_branch_not_default(*, branch: str, default_branch: str) -> dict[str, Any]:
    if branch in PROTECTED_DEFAULT_BRANCHES or branch == default_branch:
        return {
            "ok": False,
            "error": "direct_default_branch_push_blocked",
            "branch": branch,
            "default_branch": default_branch,
        }
    return {"ok": True, "branch": branch, "default_branch": default_branch}


def get_default_branch_sha(token: str, *, owner: str, repo: str, default_branch: str) -> dict[str, Any]:
    if _certification_mode():
        return {"ok": True, "sha": "cert-base-sha", "branch": default_branch}
    result = request_github(token, "GET", f"/repos/{owner}/{repo}/git/ref/heads/{default_branch}")
    if result.get("ok"):
        data = result.get("data") or {}
        obj = data.get("object") if isinstance(data, dict) else {}
        sha = obj.get("sha") if isinstance(obj, dict) else None
        if sha:
            return {"ok": True, "sha": sha, "branch": default_branch}
    return {"ok": False, "error": result.get("error") or "default branch not found"}


def ensure_feature_branch(
    token: str,
    *,
    owner: str,
    repo: str,
    branch: str,
    base_sha: str,
) -> dict[str, Any]:
    if _certification_mode():
        return {"ok": True, "created": True, "branch": branch}
    existing = request_github(token, "GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
    if existing.get("ok"):
        return {"ok": True, "created": False, "branch": branch, "idempotent": True}
    result = request_github(
        token,
        "POST",
        f"/repos/{owner}/{repo}/git/refs",
        json_body={"ref": f"refs/heads/{branch}", "sha": base_sha},
    )
    if result.get("ok"):
        return {"ok": True, "created": True, "branch": branch}
    error_text = str(result.get("error") or "")
    if result.get("http_status") == 422 and "already exists" in error_text.lower():
        return {"ok": True, "created": False, "branch": branch, "already_exists": True}
    return {"ok": False, "error": error_text}


def _file_sha_on_branch(
    token: str,
    *,
    owner: str,
    repo: str,
    path: str,
    branch: str,
) -> str | None:
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/contents/{path}",
        params={"ref": branch},
    )
    if result.get("ok"):
        data = result.get("data") or {}
        if isinstance(data, dict):
            return str(data.get("sha") or "") or None
    return None


def put_file_on_branch(
    token: str,
    *,
    owner: str,
    repo: str,
    path: str,
    content: str,
    branch: str,
    message: str,
) -> dict[str, Any]:
    if _certification_mode():
        return {"ok": True, "path": path, "commit_sha": f"cert-{path[:8]}", "simulated": True}
    body: dict[str, object] = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    sha = _file_sha_on_branch(token, owner=owner, repo=repo, path=path, branch=branch)
    if sha:
        body["sha"] = sha
    result = request_github(
        token,
        "PUT",
        f"/repos/{owner}/{repo}/contents/{path}",
        json_body=body,
    )
    if result.get("ok"):
        data = result.get("data") or {}
        commit = data.get("commit") if isinstance(data, dict) else {}
        commit_sha = commit.get("sha") if isinstance(commit, dict) else None
        return {"ok": True, "path": path, "commit_sha": commit_sha}
    return {"ok": False, "path": path, "error": result.get("error")}


def push_workspace_files_to_branch(
    *,
    token: str,
    repository: str,
    plan_id: str,
    branch: str,
    files: list[str],
    default_branch: str,
    commit_message: str,
) -> dict[str, Any]:
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {"ok": False, "error": "invalid_repository"}

    guard = assert_feature_branch_not_default(branch=branch, default_branch=default_branch)
    if not guard.get("ok"):
        return guard

    base = get_default_branch_sha(token, owner=owner, repo=repo, default_branch=default_branch)
    if not base.get("ok"):
        return {"ok": False, "error": base.get("error"), "phase": "resolve_base"}

    created = ensure_feature_branch(
        token,
        owner=owner,
        repo=repo,
        branch=branch,
        base_sha=str(base.get("sha") or ""),
    )
    if not created.get("ok"):
        return {"ok": False, "error": created.get("error"), "phase": "create_branch"}

    tree = workspace_tree_root(plan_id=plan_id)
    if not tree.is_dir():
        return {"ok": False, "error": "workspace_tree_missing", "phase": "workspace"}

    commits: list[dict[str, Any]] = []
    errors: list[str] = []
    for rel in files:
        path = workspace_file_path(plan_id=plan_id, rel=rel)
        if not path or not path.is_file():
            errors.append(f"{rel}:missing_in_workspace")
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        put = put_file_on_branch(
            token,
            owner=owner,
            repo=repo,
            path=rel,
            content=content,
            branch=branch,
            message=commit_message,
        )
        if put.get("ok"):
            commits.append(put)
        else:
            errors.append(f"{rel}:{put.get('error')}")

    if errors:
        return {
            "ok": False,
            "errors": errors,
            "commits": commits,
            "branch": branch,
            "branch_created": created.get("created"),
        }
    return {
        "ok": True,
        "branch": branch,
        "default_branch": default_branch,
        "branch_created": created.get("created"),
        "commits": commits,
        "files_pushed": [c.get("path") for c in commits],
        "head_commit_sha": commits[-1].get("commit_sha") if commits else base.get("sha"),
    }
