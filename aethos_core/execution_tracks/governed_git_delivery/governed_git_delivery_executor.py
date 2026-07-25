# SPDX-License-Identifier: Apache-2.0
"""FIX 336 — bounded Git delivery executor."""

from __future__ import annotations

import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_executor import (
    verify_code_generation,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    list_changeset_registry_entries,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_contract import (
    DELIVERY_BRANCH_PREFIX,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    all_delivery_reviews_recorded,
    append_governed_git_delivery_record,
    has_git_delivery_decision_approve,
    has_git_delivery_executed,
    latest_record_by_kind,
    register_delivery_entry,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    list_workspace_registry_entries,
)

_SAFE_RX = re.compile(r"[^a-zA-Z0-9._-]+")


def _certification_mode() -> bool:
    return os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}


def _run_git(cwd: Path, *args: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "stdout": (proc.stdout or "").strip(),
            "stderr": (proc.stderr or "").strip(),
            "returncode": proc.returncode,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "stderr": str(exc), "returncode": -1}


def _safe_work_item(value: str) -> str:
    cleaned = _SAFE_RX.sub("-", str(value or "").strip()).strip("-")
    return cleaned[:48] or "work-item"


def _delivery_branch_name(*, work_item: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"{DELIVERY_BRANCH_PREFIX}/{_safe_work_item(work_item)}/{stamp}"


def _resolve_delivery_context(*, session_id: str) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    workspaces = [
        row for row in list_workspace_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    changesets = [
        row for row in list_changeset_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    if not workspaces:
        blockers.append("approved_workspace_required")
    if not changesets:
        blockers.append("approved_changeset_required")
    verification = verify_code_generation(session_id=session_id)
    if not verification.get("verified"):
        blockers.append("generation_verification_required")
    if not all_delivery_reviews_recorded(session_id=session_id):
        blockers.append("delivery_review_gates_incomplete")
    if not has_git_delivery_decision_approve(session_id=session_id):
        blockers.append("git_delivery_decision_approve_required")

    if blockers:
        return None, blockers

    workspace = workspaces[-1]
    changeset = changesets[-1]
    intake = latest_record_by_kind(session_id=session_id, kind="git_delivery_review_note")
    metadata = dict((intake or {}).get("metadata") or {})
    work_item = str(
        metadata.get("work_item")
        or metadata.get("feature")
        or changeset.get("plan_id")
        or "work-item"
    )
    return {
        "workspace": workspace,
        "changeset": changeset,
        "workspace_path": workspace.get("local_workspace_path"),
        "work_item": work_item,
        "target_branch": str(metadata.get("target_branch") or metadata.get("base_branch") or "main"),
        "repository": str(metadata.get("repository") or metadata.get("repo") or ""),
        "changeset_id": changeset.get("changeset_id"),
    }, blockers


def execute_git_delivery(*, session_id: str) -> dict[str, Any]:
    if has_git_delivery_executed(session_id=session_id):
        return {
            "ok": False,
            "executed": False,
            "error": "delivery_already_executed",
            "detail": "Git delivery already executed for this session",
        }

    context, blockers = _resolve_delivery_context(session_id=session_id)
    if context is None:
        return {
            "ok": False,
            "executed": False,
            "blockers": blockers,
            "detail": "Git delivery blocked — workspace, changeset, reviews, and approval required",
        }

    workspace_path = Path(str(context.get("workspace_path") or ""))
    if not workspace_path.is_dir():
        return {
            "ok": False,
            "executed": False,
            "blockers": ["invalid_workspace_path"],
            "detail": "Workspace path missing or invalid",
        }

    changeset = context["changeset"]
    files = [str(p) for p in (changeset.get("new_files") or []) + (changeset.get("modified_files") or [])]
    if not files:
        return {
            "ok": False,
            "executed": False,
            "blockers": ["empty_changeset"],
            "detail": "No files in approved changeset",
        }

    branch_name = _delivery_branch_name(work_item=str(context.get("work_item") or "work-item"))
    target_branch = str(context.get("target_branch") or "main")

    if not (workspace_path / ".git").exists():
        init = _run_git(workspace_path, "init")
        if not init.get("ok"):
            return {"ok": False, "executed": False, "error": "git_init_failed", "detail": init.get("stderr")}

    _run_git(workspace_path, "config", "user.email", "aethos-delivery@local")
    _run_git(workspace_path, "config", "user.name", "AethOS Governed Delivery")

    checkout = _run_git(workspace_path, "checkout", "-B", branch_name)
    if not checkout.get("ok"):
        return {
            "ok": False,
            "executed": False,
            "error": "branch_creation_failed",
            "detail": checkout.get("stderr"),
        }

    for rel in files:
        _run_git(workspace_path, "add", rel)

    commit_message = (
        f"feat({context.get('work_item')}): governed delivery from EXECUTION_TRACK_2 changeset "
        f"{context.get('changeset_id')}"
    )
    commit = _run_git(workspace_path, "commit", "-m", commit_message)
    if not commit.get("ok"):
        return {
            "ok": False,
            "executed": False,
            "error": "commit_creation_failed",
            "detail": commit.get("stderr") or commit.get("stdout"),
        }

    rev = _run_git(workspace_path, "rev-parse", "HEAD")
    commit_hash = rev.get("stdout") if rev.get("ok") else None

    push_receipt: dict[str, Any]
    if _certification_mode() or not context.get("repository"):
        push_receipt = {
            "ok": True,
            "simulated": True,
            "branch": branch_name,
            "remote_branch_ref": f"refs/heads/{branch_name}",
            "detail": "Push simulated — certification mode or no repository configured",
        }
    else:
        push = _run_git(workspace_path, "push", "-u", "origin", branch_name)
        push_receipt = {
            "ok": push.get("ok", False),
            "simulated": False,
            "branch": branch_name,
            "remote_branch_ref": f"refs/heads/{branch_name}" if push.get("ok") else None,
            "detail": push.get("stderr") or push.get("stdout") or "push attempted",
        }

    pr_receipt: dict[str, Any]
    repository = str(context.get("repository") or "")
    if _certification_mode() or not repository:
        pr_receipt = {
            "ok": True,
            "simulated": True,
            "pull_request_url": f"https://github.com/{repository}/pull/0-simulated"
            if repository
            else "https://example.local/aethos/simulated-pr",
            "title": f"Governed delivery: {context.get('work_item')}",
            "base_branch": target_branch,
            "head_branch": branch_name,
        }
    else:
        pr_receipt = _create_pull_request(
            repository=repository,
            title=f"Governed delivery: {context.get('work_item')}",
            body=(
                f"Governed Git delivery from EXECUTION_TRACK_3.\n\n"
                f"Changeset: `{context.get('changeset_id')}`\n"
                f"Commit: `{commit_hash}`\n"
            ),
            head=branch_name,
            base=target_branch,
        )

    delivery_id = f"et3-del-{uuid4().hex[:10]}"
    delivery_entry = register_delivery_entry(
        entry={
            "delivery_id": delivery_id,
            "session_id": session_id,
            "changeset_id": context.get("changeset_id"),
            "workspace_id": context.get("workspace", {}).get("workspace_id"),
            "workspace_path": str(workspace_path),
            "repository": repository or None,
            "delivery_branch": branch_name,
            "target_branch": target_branch,
            "commit_hash": commit_hash,
            "changed_files": files,
            "push_receipt": push_receipt,
            "pull_request_receipt": pr_receipt,
            "merge_performed": False,
            "deployment_performed": False,
            "review_status": "PENDING_HUMAN_REVIEW",
        }
    )

    receipt = {
        "delivery_id": delivery_id,
        "branch_name": branch_name,
        "commit_hash": commit_hash,
        "changed_files": files,
        "push_receipt": push_receipt,
        "pull_request_receipt": pr_receipt,
        "merge_performed": False,
        "deployment_performed": False,
    }

    append_governed_git_delivery_record(
        session_id=session_id,
        kind="git_delivery_executed_note",
        content=f"Git delivery executed on branch {branch_name} commit {commit_hash}",
        metadata=receipt,
    )

    return {
        "ok": True,
        "executed": True,
        "delivery": delivery_entry,
        "receipt": receipt,
        "detail": f"Delivered {len(files)} files on branch {branch_name}",
    }


def _create_pull_request(
    *,
    repository: str,
    title: str,
    body: str,
    head: str,
    base: str,
) -> dict[str, Any]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("AETHOS_GITHUB_TOKEN") or ""
    if not token:
        return {
            "ok": True,
            "simulated": True,
            "pull_request_url": f"https://github.com/{repository}/pull/0-no-token",
            "title": title,
            "base_branch": base,
            "head_branch": head,
            "detail": "PR simulated — no GitHub token configured",
        }
    try:
        from aethos_core.software_delivery.github_pr_open_mutation import open_governed_pull_request

        opened = open_governed_pull_request(
            token=token,
            repository=repository,
            title=title,
            body=body,
            head=head,
            base=base,
        )
        if opened.get("ok"):
            return {
                "ok": True,
                "simulated": opened.get("simulated", False),
                "pull_request_url": opened.get("url"),
                "pull_request_number": opened.get("number"),
                "title": title,
                "base_branch": base,
                "head_branch": head,
            }
        return {
            "ok": False,
            "simulated": False,
            "error": opened.get("error"),
            "title": title,
            "base_branch": base,
            "head_branch": head,
        }
    except Exception as exc:
        return {
            "ok": False,
            "simulated": False,
            "error": str(exc),
            "title": title,
            "base_branch": base,
            "head_branch": head,
        }


def verify_git_delivery(*, session_id: str) -> dict[str, Any]:
    entries = [
        row
        for row in __import__(
            "aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store",
            fromlist=["list_delivery_registry_entries"],
        ).list_delivery_registry_entries()
        if str(row.get("session_id") or "") == session_id
    ]
    if not entries:
        return {
            "ok": False,
            "verified": False,
            "failure_class": "delivery_missing",
            "detail": "No delivery registry entry for session",
        }

    entry = entries[-1]
    workspace_path = Path(str(entry.get("workspace_path") or ""))
    branch = str(entry.get("delivery_branch") or "")
    commit_hash = str(entry.get("commit_hash") or "")

    branch_exists = False
    commit_exists = False
    if workspace_path.is_dir() and (workspace_path / ".git").exists():
        branch_check = _run_git(workspace_path, "rev-parse", "--verify", f"refs/heads/{branch}")
        branch_exists = branch_check.get("ok", False)
        if commit_hash:
            commit_check = _run_git(workspace_path, "cat-file", "-t", commit_hash)
            commit_exists = commit_check.get("ok", False) and commit_check.get("stdout") == "commit"

    pr_receipt = entry.get("pull_request_receipt") or {}
    pr_exists = bool(pr_receipt.get("pull_request_url"))

    repository_healthy = branch_exists and commit_exists and pr_exists
    ok = repository_healthy and entry.get("merge_performed") is False

    return {
        "ok": ok,
        "verified": ok,
        "delivery_id": entry.get("delivery_id"),
        "branch_exists": branch_exists,
        "commit_exists": commit_exists,
        "pull_request_exists": pr_exists,
        "repository_healthy": repository_healthy,
        "merge_performed": entry.get("merge_performed") is True,
        "failure_class": "" if ok else "verification_failed",
        "detail": "Git delivery verification passed" if ok else "Git delivery verification failed",
    }
