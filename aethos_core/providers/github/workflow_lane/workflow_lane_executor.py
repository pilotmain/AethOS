# SPDX-License-Identifier: Apache-2.0
"""Workflow Lane Executor — governed branch/file/commit/PR creation via GitHub API.

Executes the workflow-file creation plan after explicit user approval.
Uses GitHub's Git Data API for branch creation and Contents API for file commit.

Idempotent: each step checks current state before acting. Safe to retry
after partial failure without duplicating branches, commits, or PRs.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo, request_github

logger = logging.getLogger(__name__)


def execute_workflow_file_creation(
    token: str,
    *,
    repo: str,
    file_path: str,
    branch: str,
    base_branch: str,
    yaml_content: str,
    commit_message: str = "Add CI workflow scaffold",
    prior_progress: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute the governed workflow file creation plan (idempotent).

    Each step checks whether it has already completed before acting.
    Safe to call multiple times after partial failure.

    Returns a dict with 'ok', 'detail', and 'progress' tracking all steps.
    """
    owner, repo_name = parse_owner_repo(repo)
    if not owner or not repo_name:
        return _fail("Invalid repository format. Expected owner/repo.", step="validate", progress=_empty_progress())

    if not yaml_content.strip():
        return _fail("YAML content is empty.", step="validate", progress=_empty_progress())

    progress: dict[str, Any] = dict(prior_progress) if prior_progress else _empty_progress()
    progress["execution_attempts"] = progress.get("execution_attempts", 0) + 1

    # Step 1: Verify file does not already exist on base branch (skip if branch already created)
    if not progress.get("branch_created"):
        existing = _check_file_exists(token, owner=owner, repo=repo_name, path=file_path, ref=base_branch)
        if existing.get("exists"):
            return _fail(
                f"`{file_path}` already exists on `{base_branch}`. Will not overwrite.",
                step="file_exists_check",
                progress=progress,
                detail={"sha": existing.get("sha")},
            )

    # Step 2: Get base branch SHA + create branch (idempotent)
    if not progress.get("branch_created"):
        base_sha = _get_branch_sha(token, owner=owner, repo=repo_name, branch=base_branch)
        if not base_sha.get("ok"):
            progress["last_failed_step"] = "resolve_base_branch"
            return _fail(
                f"Cannot resolve base branch `{base_branch}`: {base_sha.get('error')}",
                step="resolve_base_branch",
                progress=progress,
            )

        branch_result = _create_branch(token, owner=owner, repo=repo_name, branch=branch, sha=base_sha["sha"])
        if branch_result.get("ok"):
            progress["branch_created"] = True
            progress["branch_name"] = branch
            progress["last_successful_step"] = "create_branch"
        elif branch_result.get("already_exists"):
            progress["branch_created"] = True
            progress["branch_name"] = branch
            progress["branch_reused"] = True
            progress["last_successful_step"] = "create_branch"
            logger.info("Branch %s already exists, reusing.", branch)
        else:
            progress["last_failed_step"] = "create_branch"
            return _fail(
                f"Cannot create branch `{branch}`: {branch_result.get('error')}",
                step="create_branch",
                progress=progress,
            )

    # Step 3: Create file (idempotent — check if already on branch)
    if not progress.get("file_committed"):
        existing_on_branch = _check_file_exists(token, owner=owner, repo=repo_name, path=file_path, ref=branch)
        if existing_on_branch.get("exists"):
            progress["file_committed"] = True
            progress["commit_sha"] = existing_on_branch.get("sha") or progress.get("commit_sha") or ""
            progress["file_reused"] = True
            progress["last_successful_step"] = "create_file"
            logger.info("File %s already exists on %s, skipping commit.", file_path, branch)
        else:
            file_result = _create_file(
                token,
                owner=owner,
                repo=repo_name,
                path=file_path,
                content=yaml_content,
                branch=branch,
                message=commit_message,
            )
            if file_result.get("ok"):
                progress["file_committed"] = True
                progress["commit_sha"] = file_result.get("commit_sha") or ""
                progress["commit_created"] = True
                progress["last_successful_step"] = "create_file"
            else:
                progress["last_failed_step"] = "create_file"
                return _fail(
                    f"Cannot create file `{file_path}`: {file_result.get('error')}",
                    step="create_file",
                    progress=progress,
                )

    # Step 4: Open PR (idempotent — check if already open)
    if not progress.get("pr_opened"):
        pr_result = _open_pull_request(
            token,
            owner=owner,
            repo=repo_name,
            head=branch,
            base=base_branch,
            title=commit_message,
            body=_pr_body(file_path, branch, base_branch),
        )
        if pr_result.get("ok"):
            progress["pr_opened"] = True
            progress["pr_url"] = pr_result.get("url") or ""
            progress["pr_number"] = pr_result.get("number")
            progress["pr_reused"] = False
            progress["last_successful_step"] = "open_pr"
        elif pr_result.get("already_exists"):
            progress["pr_opened"] = True
            progress["pr_url"] = pr_result.get("existing_url") or ""
            progress["pr_number"] = pr_result.get("existing_number")
            progress["pr_reused"] = True
            progress["last_successful_step"] = "open_pr"
            logger.info("PR already exists, reusing.")
        else:
            progress["last_failed_step"] = "open_pr"
            return _fail(
                f"File committed on `{branch}` but PR creation failed: {pr_result.get('error')}",
                step="open_pr",
                progress=progress,
            )

    return _success(
        detail=f"Workflow file created on `{branch}` and PR opened to `{base_branch}`.",
        progress=progress,
    )


# ─── Progress Helpers ────────────────────────────────────────────────────────

def _empty_progress() -> dict[str, Any]:
    return {
        "branch_created": False,
        "branch_name": "",
        "branch_reused": False,
        "commit_created": False,
        "commit_sha": "",
        "file_committed": False,
        "file_reused": False,
        "pr_opened": False,
        "pr_number": None,
        "pr_url": "",
        "pr_reused": False,
        "workflow_run_detected": False,
        "last_successful_step": None,
        "last_failed_step": None,
        "execution_attempts": 0,
    }


# ─── GitHub API Helpers ──────────────────────────────────────────────────────

def _check_file_exists(
    token: str, *, owner: str, repo: str, path: str, ref: str
) -> dict[str, Any]:
    result = request_github(token, "GET", f"/repos/{owner}/{repo}/contents/{path}", params={"ref": ref})
    if result.get("ok"):
        data = result.get("data") or {}
        return {"exists": True, "sha": data.get("sha") if isinstance(data, dict) else None}
    status = result.get("http_status")
    if status == 404:
        return {"exists": False}
    return {"exists": False, "error": result.get("error")}


def _get_branch_sha(token: str, *, owner: str, repo: str, branch: str) -> dict[str, Any]:
    result = request_github(token, "GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
    if result.get("ok"):
        data = result.get("data") or {}
        obj = data.get("object") if isinstance(data, dict) else {}
        sha = obj.get("sha") if isinstance(obj, dict) else None
        if sha:
            return {"ok": True, "sha": sha}
    return {"ok": False, "error": result.get("error") or "Branch not found"}


def _create_branch(
    token: str, *, owner: str, repo: str, branch: str, sha: str
) -> dict[str, Any]:
    result = request_github(
        token,
        "POST",
        f"/repos/{owner}/{repo}/git/refs",
        json_body={"ref": f"refs/heads/{branch}", "sha": sha},
    )
    if result.get("ok"):
        return {"ok": True}
    error_text = str(result.get("error") or "")
    if result.get("http_status") == 422 and "reference already exists" in error_text.lower():
        return {"ok": False, "already_exists": True, "error": error_text}
    return {"ok": False, "already_exists": False, "error": error_text}


def _create_file(
    token: str,
    *,
    owner: str,
    repo: str,
    path: str,
    content: str,
    branch: str,
    message: str,
) -> dict[str, Any]:
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    result = request_github(
        token,
        "PUT",
        f"/repos/{owner}/{repo}/contents/{path}",
        json_body={
            "message": message,
            "content": encoded,
            "branch": branch,
        },
    )
    if result.get("ok"):
        data = result.get("data") or {}
        commit = data.get("commit") if isinstance(data, dict) else {}
        commit_sha = commit.get("sha") if isinstance(commit, dict) else None
        return {"ok": True, "commit_sha": commit_sha}
    error_text = str(result.get("error") or "")
    if result.get("http_status") == 422 and "sha" in error_text.lower():
        return {"ok": False, "error": "File already exists on target branch."}
    return {"ok": False, "error": error_text}


def _open_pull_request(
    token: str,
    *,
    owner: str,
    repo: str,
    head: str,
    base: str,
    title: str,
    body: str,
) -> dict[str, Any]:
    result = request_github(
        token,
        "POST",
        f"/repos/{owner}/{repo}/pulls",
        json_body={
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        },
    )
    if result.get("ok"):
        data = result.get("data") or {}
        pr_url = data.get("html_url") if isinstance(data, dict) else None
        pr_number = data.get("number") if isinstance(data, dict) else None
        return {"ok": True, "url": pr_url, "number": pr_number}
    error_text = str(result.get("error") or "")
    if result.get("http_status") == 422 and "already exists" in error_text.lower():
        existing = _find_existing_pr(token, owner=owner, repo=repo, head=head, base=base)
        return {
            "ok": False,
            "already_exists": True,
            "error": error_text,
            "existing_url": existing.get("url"),
            "existing_number": existing.get("number"),
        }
    return {"ok": False, "already_exists": False, "error": error_text}


def _find_existing_pr(
    token: str, *, owner: str, repo: str, head: str, base: str
) -> dict[str, Any]:
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/pulls",
        params={"head": f"{owner}:{head}", "base": base, "state": "open"},
    )
    if result.get("ok"):
        data = result.get("data")
        if isinstance(data, list) and data:
            pr = data[0]
            return {"url": pr.get("html_url"), "number": pr.get("number")}
    return {}


def _pr_body(file_path: str, branch: str, base_branch: str) -> str:
    return (
        f"## Governed Workflow File Creation\n\n"
        f"- **File:** `{file_path}`\n"
        f"- **Branch:** `{branch}`\n"
        f"- **Target:** `{base_branch}`\n"
        f"- **Risk tier:** T2 (feature branch + PR)\n\n"
        f"Created by AethOS governed mutation pipeline.\n\n"
        f"### Verification\n"
        f"- [ ] Workflow file exists after merge\n"
        f"- [ ] GitHub Actions run triggers\n"
        f"- [ ] No unrelated file modifications\n"
    )


# ─── Result Helpers ──────────────────────────────────────────────────────────

def _success(*, detail: str, progress: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "detail": detail,
        "pr_url": progress.get("pr_url") or "",
        "pr_number": progress.get("pr_number"),
        "commit_sha": progress.get("commit_sha") or "",
        "branch": progress.get("branch_name") or "",
        "reused_pr": progress.get("pr_reused", False),
        "operation": "workflow_file_creation",
        "risk_tier": "T2",
        "progress": progress,
    }


def _fail(
    message: str,
    *,
    step: str,
    progress: dict[str, Any],
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "detail": message,
        "step": step,
        "operation": "workflow_file_creation",
        "risk_tier": "T2",
        "progress": progress,
        **(detail or {}),
    }
