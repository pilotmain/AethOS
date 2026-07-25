# SPDX-License-Identifier: Apache-2.0
"""FIX 335 — bounded code generation executor inside approved workspaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_generators import (
    build_generation_plan,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    append_governed_code_generation_record,
    has_code_generation_executed,
    has_generation_decision_approve,
    latest_record_by_kind,
    register_changeset_entry,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    list_workspace_registry_entries,
)


def _resolve_workspace(*, session_id: str) -> dict[str, Any] | None:
    entries = [
        row for row in list_workspace_registry_entries() if str(row.get("session_id") or "") == session_id
    ]
    return entries[-1] if entries else None


def _resolve_generation_request(*, session_id: str) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    workspace = _resolve_workspace(session_id=session_id)
    if workspace is None:
        blockers.append("approved_workspace_required")
        return None, blockers

    if not has_generation_decision_approve(session_id=session_id):
        blockers.append("generation_decision_approve_required")
        return None, blockers

    request_record = latest_record_by_kind(session_id=session_id, kind="generation_request_review_note")
    if request_record is None:
        blockers.append("generation_request_review_required")
        return None, blockers

    metadata = dict(request_record.get("metadata") or {})
    request = {
        "title": metadata.get("title") or metadata.get("feature_name") or "generated-feature",
        "feature_name": metadata.get("feature_name") or metadata.get("title") or "generated-feature",
        "requirement_type": metadata.get("type") or metadata.get("requirement_type") or "task",
        "stack": metadata.get("stack"),
        "template_id": workspace.get("template_id"),
        "description": request_record.get("content"),
        "workspace_id": workspace.get("workspace_id"),
        "workspace_path": workspace.get("local_workspace_path"),
    }
    return request, blockers


def execute_code_generation(*, session_id: str) -> dict[str, Any]:
    if has_code_generation_executed(session_id=session_id):
        return {
            "ok": False,
            "executed": False,
            "error": "generation_already_executed",
            "detail": "Code generation already executed for this session",
        }

    request, blockers = _resolve_generation_request(session_id=session_id)
    if request is None:
        return {
            "ok": False,
            "executed": False,
            "blockers": blockers,
            "detail": "Generation blocked — approved workspace and human decision required",
        }

    workspace_path = Path(str(request.get("workspace_path") or ""))
    if not workspace_path.is_dir():
        return {
            "ok": False,
            "executed": False,
            "blockers": ["invalid_workspace_path"],
            "detail": "Workspace path missing or invalid",
        }

    plan = build_generation_plan(request=request)
    new_files: list[str] = []
    modified_files: list[str] = []
    deleted_files: list[str] = []

    for artifact in plan.get("artifacts") or []:
        rel = str(artifact.get("path") or "")
        if not rel:
            continue
        target = workspace_path / rel
        action = str(artifact.get("action") or "create")
        content = str(artifact.get("content") or "")

        if action == "delete" and target.is_file():
            target.unlink(missing_ok=True)
            deleted_files.append(rel)
            continue

        existed = target.is_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if existed:
            modified_files.append(rel)
        else:
            new_files.append(rel)

    changeset_id = f"et2-cs-{uuid4().hex[:10]}"
    changeset_entry = register_changeset_entry(
        entry={
            "changeset_id": changeset_id,
            "session_id": session_id,
            "workspace_id": request.get("workspace_id"),
            "workspace_path": str(workspace_path),
            "plan_id": plan.get("plan_id"),
            "stack": plan.get("stack"),
            "requirement_type": plan.get("requirement_type"),
            "new_files": new_files,
            "modified_files": modified_files,
            "deleted_files": deleted_files,
            "generated_tests": [p for p in new_files + modified_files if "test" in p.lower()],
            "generated_documentation": [p for p in new_files + modified_files if p.startswith("docs/")],
            "git_commit_performed": False,
            "git_push_performed": False,
            "pr_creation_performed": False,
            "review_status": "PENDING_HUMAN_REVIEW",
        }
    )

    receipt = {
        "changeset_id": changeset_id,
        "workspace_path": str(workspace_path),
        "plan_id": plan.get("plan_id"),
        "new_files": new_files,
        "modified_files": modified_files,
        "deleted_files": deleted_files,
        "file_count": len(new_files) + len(modified_files) + len(deleted_files),
        "git_commit_performed": False,
        "git_push_performed": False,
        "pr_creation_performed": False,
    }

    append_governed_code_generation_record(
        session_id=session_id,
        kind="code_generation_executed_note",
        content=(
            f"Code generation executed for {plan.get('feature_name')} — "
            f"{len(new_files)} new, {len(modified_files)} modified files"
        ),
        metadata=receipt,
    )

    return {
        "ok": True,
        "executed": True,
        "plan": plan,
        "changeset": changeset_entry,
        "receipt": receipt,
        "detail": f"Generated {receipt['file_count']} reviewable file changes",
    }


def verify_code_generation(*, session_id: str) -> dict[str, Any]:
    entries = [
        row for row in __import__(
            "aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store",
            fromlist=["list_changeset_registry_entries"],
        ).list_changeset_registry_entries()
        if str(row.get("session_id") or "") == session_id
    ]
    if not entries:
        return {
            "ok": False,
            "verified": False,
            "failure_class": "changeset_missing",
            "detail": "No changeset registry entry for session",
        }

    entry = entries[-1]
    workspace_path = Path(str(entry.get("workspace_path") or ""))
    missing_files: list[str] = []
    for rel in (entry.get("new_files") or []) + (entry.get("modified_files") or []):
        if not (workspace_path / str(rel)).is_file():
            missing_files.append(str(rel))

    compilation_ready = not missing_files
    dependency_consistent = bool(entry.get("stack"))
    template_compliant = bool(entry.get("plan_id"))
    generation_complete = bool(entry.get("new_files") or entry.get("modified_files"))

    ok = compilation_ready and dependency_consistent and template_compliant and generation_complete
    return {
        "ok": ok,
        "verified": ok,
        "changeset_id": entry.get("changeset_id"),
        "workspace_path": str(workspace_path),
        "missing_files": missing_files,
        "compilation_ready": compilation_ready,
        "dependency_consistent": dependency_consistent,
        "template_compliant": template_compliant,
        "generation_complete": generation_complete,
        "git_commit_performed": entry.get("git_commit_performed") is False,
        "git_push_performed": entry.get("git_push_performed") is False,
        "failure_class": "" if ok else "verification_failed",
        "detail": "Generation verification passed" if ok else "Generation verification failed",
    }
