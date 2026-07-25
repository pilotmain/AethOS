# SPDX-License-Identifier: Apache-2.0
"""Terminal preflight — proposal before bounded execution."""

from __future__ import annotations

from time import time
from typing import Any
from uuid import uuid4

from aethos_core.workspace_runtime.workspace_artifacts import store_workspace_runtime_artifact
from aethos_core.workspace_runtime.workspace_policy import evaluate_command_policy
from aethos_core.workspace_runtime.workspace_sessions import create_workspace_session


def run_terminal_preflight(
    *,
    command: str,
    workspace_id: str | None = None,
    workspace_hint: str | None = None,
    cwd: str | None = None,
) -> dict[str, Any]:
    policy = evaluate_command_policy(command)
    preflight_id = f"tpf-{uuid4().hex[:12]}"
    session = create_workspace_session(workspace_id=workspace_id, kind="terminal")

    resolved_cwd = cwd
    if not resolved_cwd:
        from aethos_core.workspace_runtime.workspace_registry import resolve_workspace

        row = resolve_workspace(workspace_id, workspace_hint)
        if row:
            resolved_cwd = str(row.get("path"))
        else:
            try:
                from aethos_core.local_workspace.readonly.actions import _repo_from_hint

                resolved_cwd = str(_repo_from_hint(workspace_hint or "aethos", session_id="default"))
            except Exception:
                resolved_cwd = None

    if not policy.get("allowed"):
        denial = store_workspace_runtime_artifact(
            artifact_type="workspace_policy_denial",
            workspace_id=workspace_id,
            session_id=session["session_id"],
            payload={"command": command, "policy": policy},
            summary=f"Policy denial: {policy.get('error')}",
        )
        record = {
            "ok": False,
            "preflight_id": preflight_id,
            "status": "policy_denied",
            "policy": policy,
            "denial_artifact_id": denial.get("artifact_id"),
            "session_id": session["session_id"],
            "execution_enabled": False,
        }
        _persist_preflight(preflight_id, record)
        return record

    record = {
        "ok": True,
        "preflight_id": preflight_id,
        "status": "pending_approval",
        "command": command.strip(),
        "cwd": resolved_cwd,
        "workspace_id": workspace_id,
        "workspace_hint": workspace_hint,
        "session_id": session["session_id"],
        "policy": policy,
        "approval_required": True,
        "execution_enabled": False,
        "autonomous_execution_blocked": True,
        "created_at": time(),
    }
    _persist_preflight(preflight_id, record)
    return record


def _persist_preflight(preflight_id: str, record: dict[str, Any]) -> None:
    from aethos_core.workspace_runtime.terminal.terminal_preflight_store import save_terminal_preflight

    save_terminal_preflight(preflight_id, record)
