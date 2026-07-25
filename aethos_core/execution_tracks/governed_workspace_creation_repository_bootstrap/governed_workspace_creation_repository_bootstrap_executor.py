# SPDX-License-Identifier: Apache-2.0
"""FIX 334 — bounded local repository bootstrap executor."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    append_governed_workspace_creation_record,
    has_workspace_bootstrap_executed,
    has_workspace_decision_approve,
    latest_record_by_kind,
    register_workspace_entry,
    workspace_bootstrap_root,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_templates import (
    get_project_template,
    render_template_files,
)

_SAFE_NAME_RX = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_segment(value: str) -> str:
    cleaned = _SAFE_NAME_RX.sub("-", str(value or "").strip()).strip("-")
    return cleaned[:64] or "workspace"


def _resolve_bootstrap_request(*, session_id: str) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    if not has_workspace_decision_approve(session_id=session_id):
        blockers.append("workspace_decision_approve_required")
        return None, blockers

    creation = latest_record_by_kind(session_id=session_id, kind="workspace_creation_review_note")
    if creation is None:
        blockers.append("workspace_creation_review_required")
        return None, blockers

    metadata = dict(creation.get("metadata") or {})
    workspace_name = str(metadata.get("workspace_name") or metadata.get("name") or "governed-workspace")
    template_id = str(metadata.get("template_id") or metadata.get("template") or "generic_repository")
    if get_project_template(template_id) is None:
        blockers.append(f"unsupported_template:{template_id}")
        return None, blockers

    return {
        "workspace_name": workspace_name,
        "template_id": template_id,
        "org_id": str(metadata.get("org_id") or metadata.get("organization_id") or ""),
        "tenant_id": str(metadata.get("tenant_id") or ""),
        "project_name": str(metadata.get("project_name") or workspace_name),
        "creation_record_id": creation.get("record_id"),
    }, blockers


def execute_repository_bootstrap(*, session_id: str) -> dict[str, Any]:
    if has_workspace_bootstrap_executed(session_id=session_id):
        return {
            "ok": False,
            "executed": False,
            "error": "bootstrap_already_executed",
            "detail": "Bootstrap already executed for this session",
        }

    request, blockers = _resolve_bootstrap_request(session_id=session_id)
    if request is None:
        return {
            "ok": False,
            "executed": False,
            "blockers": blockers,
            "detail": "Bootstrap blocked — human approval and workspace review required",
        }

    template = get_project_template(request["template_id"])
    assert template is not None

    workspace_id = f"et1-ws-{uuid4().hex[:10]}"
    workspace_name = request["workspace_name"]
    safe_name = _safe_segment(workspace_name)
    workspace_path = (workspace_bootstrap_root() / session_id / safe_name).resolve()
    workspace_path.mkdir(parents=True, exist_ok=True)

    created_folders: list[str] = []
    for folder in template.get("folders") or []:
        target = workspace_path / str(folder)
        target.mkdir(parents=True, exist_ok=True)
        created_folders.append(str(folder))

    created_files: list[str] = []
    for rel, content in render_template_files(
        workspace_name=workspace_name,
        template_id=request["template_id"],
        session_id=session_id,
    ).items():
        target = workspace_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        created_files.append(rel)

    registry_entry = register_workspace_entry(
        entry={
            "workspace_id": workspace_id,
            "session_id": session_id,
            "workspace_name": workspace_name,
            "local_workspace_path": str(workspace_path),
            "template_id": request["template_id"],
            "org_id": request.get("org_id") or None,
            "tenant_id": request.get("tenant_id") or None,
            "project_name": request.get("project_name"),
            "repository_association": "local_bootstrap_only",
            "health_state": "bootstrapped",
            "git_push_performed": False,
            "deployment_performed": False,
        }
    )

    receipt = {
        "workspace_id": workspace_id,
        "workspace_path": str(workspace_path),
        "template_id": request["template_id"],
        "folders_created": created_folders,
        "files_created": created_files,
        "git_push_performed": False,
        "deployment_performed": False,
        "provider_mutation_performed": False,
        "trust_mutation_performed": False,
    }

    append_governed_workspace_creation_record(
        session_id=session_id,
        kind="workspace_bootstrap_executed_note",
        content=f"Repository bootstrap executed for {workspace_name} using template {request['template_id']}",
        metadata=receipt,
    )

    return {
        "ok": True,
        "executed": True,
        "registry_entry": registry_entry,
        "receipt": receipt,
        "detail": f"Bootstrapped {len(created_folders)} folders and {len(created_files)} files",
    }


def verify_workspace_bootstrap(*, session_id: str) -> dict[str, Any]:
    entries = [
        row
        for row in __import__(
            "aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store",
            fromlist=["list_workspace_registry_entries"],
        ).list_workspace_registry_entries()
        if str(row.get("session_id") or "") == session_id
    ]
    if not entries:
        return {
            "ok": False,
            "verified": False,
            "failure_class": "workspace_not_bootstrapped",
            "detail": "No workspace registry entry for session",
        }

    entry = entries[-1]
    workspace_path = Path(str(entry.get("local_workspace_path") or ""))
    template_id = str(entry.get("template_id") or "")
    template = get_project_template(template_id)
    if template is None or not workspace_path.is_dir():
        return {
            "ok": False,
            "verified": False,
            "failure_class": "invalid_workspace",
            "detail": "Workspace path or template invalid",
        }

    missing_folders: list[str] = []
    for folder in template.get("folders") or []:
        if not (workspace_path / str(folder)).is_dir():
            missing_folders.append(str(folder))

    expected_files = render_template_files(
        workspace_name=str(entry.get("workspace_name") or "workspace"),
        template_id=template_id,
        session_id=session_id,
    )
    missing_files: list[str] = []
    for rel in expected_files:
        if not (workspace_path / rel).is_file():
            missing_files.append(rel)

    governance_valid = False
    governance_path = workspace_path / "aethos" / "governance-metadata.json"
    if governance_path.is_file():
        try:
            meta = json.loads(governance_path.read_text(encoding="utf-8"))
            governance_valid = meta.get("bootstrap_only") is True and meta.get("deployment_authority") is False
        except (OSError, json.JSONDecodeError):
            governance_valid = False

    ok = not missing_folders and not missing_files and governance_valid
    return {
        "ok": ok,
        "verified": ok,
        "workspace_id": entry.get("workspace_id"),
        "workspace_path": str(workspace_path),
        "missing_folders": missing_folders,
        "missing_files": missing_files,
        "governance_metadata_valid": governance_valid,
        "failure_class": "" if ok else "verification_failed",
        "detail": "Workspace verification passed" if ok else "Workspace verification failed",
    }
