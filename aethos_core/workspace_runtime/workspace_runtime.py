# SPDX-License-Identifier: Apache-2.0
"""Governed workspace runtime."""

from __future__ import annotations

from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.workspace_runtime.desktop_awareness import observe_active_windows, observe_desktop_environment, observe_process_summary
from aethos_core.workspace_runtime.workspace_artifacts import list_workspace_runtime_artifacts, store_workspace_runtime_artifact
from aethos_core.workspace_runtime.workspace_audit import list_workspace_audit, record_workspace_audit
from aethos_core.workspace_runtime.workspace_memory import record_workspace_context, workspace_memory_snapshot
from aethos_core.workspace_runtime.workspace_registry import list_active_workspaces, workspace_status
from aethos_core.workspace_runtime.workspace_sessions import list_workspace_sessions


def get_workspace_runtime_state() -> dict[str, Any]:
    return {
        "ok": True,
        "workspaces": list_active_workspaces(),
        "sessions": list_workspace_sessions(),
        "artifacts": list_workspace_runtime_artifacts(limit=20),
        "audit": list_workspace_audit(limit=15),
        "memory": workspace_memory_snapshot(),
        "desktop": {
            "windows": observe_active_windows(),
            "processes": observe_process_summary(),
        },
        "readonly": True,
        "autonomous_execution_blocked": True,
    }


def run_workspace_diagnostics(
    *,
    workspace_id: str | None = None,
    hint: str | None = None,
    user_request: str = "",
) -> dict[str, Any]:
    """Engineering diagnostics flow — readonly scan + optional validation preflight."""
    from aethos_core.workspace_runtime.workspace_registry import resolve_workspace

    row = resolve_workspace(workspace_id, hint)
    path = Path(str(row["path"])) if row else None
    if not path or not path.is_dir():
        from aethos_core.local_workspace.readonly.actions import _repo_from_hint

        path = Path(_repo_from_hint(hint or "aethos", session_id="default"))

    steps: list[dict[str, Any]] = []
    if "test" in user_request.lower() or "pytest" in user_request.lower():
        from aethos_core.local_workspace.analysis.diagnostics import analyze_test_state

        tests = analyze_test_state(path)
        steps.append({"step": "test_analysis", "result": tests})
    from aethos_core.local_workspace.readonly.actions import run_git_status_report

    git = run_git_status_report(hint=hint or (row or {}).get("name") or "aethos")
    steps.append({"step": "git_status", "result": git})

    replay_id = f"wreplay-{uuid4().hex[:12]}"
    record = store_workspace_runtime_artifact(
        artifact_type="workspace_runtime_replay",
        workspace_id=workspace_id or (row or {}).get("workspace_id"),
        payload={"steps": steps, "user_request": user_request[:300], "replay_id": replay_id},
        summary="Workspace diagnostics replay",
    )
    record_workspace_audit(
        {
            "audit_id": f"waudit-{uuid4().hex[:12]}",
            "action": "workspace_diagnostics",
            "workspace_id": workspace_id,
            "replay_id": replay_id,
            "artifact_id": record.get("artifact_id"),
        }
    )
    record_workspace_context(workspace_id=workspace_id, repo_path=str(path), replay_id=replay_id)
    return {
        "ok": True,
        "replay_id": replay_id,
        "artifact_id": record.get("artifact_id"),
        "steps": steps,
        "scanned_at": time(),
    }


def coordinate_multi_workspace(request: str, *, workspace_hints: list[str] | None = None) -> dict[str, Any]:
    """Multi-workspace readonly coordination."""
    hints = workspace_hints or ["aethos"]
    results: list[dict[str, Any]] = []
    for hint in hints[:6]:
        status = workspace_status(hint=hint)
        results.append({"hint": hint, "status": status})
    artifact = store_workspace_runtime_artifact(
        artifact_type="workspace_orchestration",
        payload={"request": request[:300], "results": results},
        summary=f"Multi-workspace scan ({len(results)} workspaces)",
    )
    return {"ok": True, "results": results, "artifact_id": artifact.get("artifact_id")}
