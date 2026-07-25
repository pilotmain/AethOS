# SPDX-License-Identifier: Apache-2.0
"""Workspace runtime API — governed desktop + terminal control."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["workspace"])


class TerminalPreflightRequest(BaseModel):
    command: str = Field(min_length=1, max_length=500)
    workspace_id: str | None = None
    workspace_hint: str | None = None
    cwd: str | None = None


class TerminalExecuteRequest(BaseModel):
    preflight_id: str
    approved: bool = True


class WorkspaceOpenRequest(BaseModel):
    app: str = Field(min_length=1, max_length=40)
    path: str | None = None
    workspace_hint: str | None = None


@router.get("/workspace/status")
def workspace_status_api(workspace_id: str | None = None, hint: str | None = None) -> dict[str, Any]:
    from aethos_core.workspace_runtime.workspace_runtime import get_workspace_runtime_state
    from aethos_core.workspace_runtime.workspace_registry import workspace_status

    return {"ok": True, "status": workspace_status(workspace_id, hint), "runtime": get_workspace_runtime_state()}


@router.get("/workspace/windows")
def workspace_windows_api() -> dict[str, Any]:
    from aethos_core.workspace_runtime.desktop_awareness import observe_active_windows

    return {"ok": True, "windows": observe_active_windows(), "readonly": True}


@router.get("/workspace/processes")
def workspace_processes_api() -> dict[str, Any]:
    from aethos_core.workspace_runtime.desktop_awareness import observe_process_summary

    return {"ok": True, "processes": observe_process_summary(), "readonly": True}


@router.get("/workspace/sessions")
def workspace_sessions_api() -> dict[str, Any]:
    from aethos_core.workspace_runtime.workspace_sessions import list_workspace_sessions
    from aethos_core.workspace_runtime.terminal.terminal_preflight_store import list_terminal_preflights

    return {
        "ok": True,
        "sessions": list_workspace_sessions(),
        "terminal_preflights": list_terminal_preflights(),
    }


@router.get("/workspace/artifacts")
def workspace_artifacts_api(limit: int = 40) -> dict[str, Any]:
    from aethos_core.workspace_runtime.workspace_artifacts import list_workspace_runtime_artifacts

    return {"ok": True, "artifacts": list_workspace_runtime_artifacts(limit=limit)}


@router.get("/workspace/artifacts/{artifact_id}")
def workspace_artifact_api(artifact_id: str) -> dict[str, Any]:
    from aethos_core.workspace_runtime.workspace_artifacts import get_workspace_runtime_artifact

    row = get_workspace_runtime_artifact(artifact_id)
    if not row:
        raise HTTPException(status_code=404, detail="artifact_not_found")
    return {"ok": True, "artifact": row}


@router.get("/workspace/audit")
def workspace_audit_api(limit: int = 40) -> dict[str, Any]:
    from aethos_core.workspace_runtime.workspace_audit import list_workspace_audit

    return {"ok": True, "audit": list_workspace_audit(limit=limit)}


@router.get("/workspace/memory")
def workspace_memory_api() -> dict[str, Any]:
    from aethos_core.workspace_runtime.workspace_memory import workspace_memory_snapshot

    return {"ok": True, "memory": workspace_memory_snapshot()}


@router.post("/workspace/terminal/preflight")
def workspace_terminal_preflight_api(body: TerminalPreflightRequest) -> dict[str, Any]:
    from aethos_core.workspace_runtime.terminal.terminal_preflight import run_terminal_preflight

    result = run_terminal_preflight(
        command=body.command,
        workspace_id=body.workspace_id,
        workspace_hint=body.workspace_hint,
        cwd=body.cwd,
    )
    return {"ok": result.get("ok", False) or result.get("status") == "policy_denied", "preflight": result}


@router.post("/workspace/terminal/execute")
def workspace_terminal_execute_api(body: TerminalExecuteRequest) -> dict[str, Any]:
    from aethos_core.workspace_runtime.terminal.terminal_executor import execute_terminal_command
    from aethos_core.workspace_runtime.terminal.terminal_preflight_store import approve_terminal_preflight, get_terminal_preflight

    preflight = get_terminal_preflight(body.preflight_id)
    if not preflight:
        raise HTTPException(status_code=404, detail="preflight_not_found")
    if body.approved:
        approve_terminal_preflight(body.preflight_id)
    execution = execute_terminal_command(preflight=preflight, approved=body.approved)
    if not execution.get("ok") and execution.get("status") not in ("approval_required", "policy_denied"):
        raise HTTPException(status_code=400, detail=execution.get("error") or execution.get("status"))
    return {"ok": execution.get("ok", False), "execution": execution, "preflight_id": body.preflight_id}


@router.post("/workspace/open")
def workspace_open_api(body: WorkspaceOpenRequest) -> dict[str, Any]:
    from aethos_core.workspace_runtime.app_adapters import open_in_application

    result = open_in_application(app=body.app, path=body.path, workspace_hint=body.workspace_hint)
    if not result.get("ok") and result.get("error") not in ("use_terminal_preflight", "code_cli_not_found", "cursor_cli_not_found"):
        raise HTTPException(status_code=400, detail=result.get("error") or "open_failed")
    return {"ok": True, "result": result}


@router.post("/workspace/diagnostics")
def workspace_diagnostics_api(
    user_request: str = "",
    workspace_id: str | None = None,
    hint: str | None = None,
) -> dict[str, Any]:
    from aethos_core.workspace_runtime.workspace_runtime import run_workspace_diagnostics

    return run_workspace_diagnostics(workspace_id=workspace_id, hint=hint, user_request=user_request)
