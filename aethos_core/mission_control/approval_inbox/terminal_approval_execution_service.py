# SPDX-License-Identifier: Apache-2.0
"""Governed terminal preflight execution from Mission Control approval inbox."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_audit_service import persist_ui_approval_audit
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox


@dataclass(frozen=True)
class TerminalApprovalExecutionResult:
    ok: bool
    session_id: str
    inbox_id: str
    preflight_id: str = ""
    execution_status: str = ""
    output: str = ""
    exit_code: int | None = None
    subagent_session_keys: list[str] = field(default_factory=list)
    agent_send_results: list[dict[str, Any]] = field(default_factory=list)
    audit_id: str = ""
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def _find_terminal_inbox_item(*, session_id: str, inbox_id: str) -> dict[str, Any] | None:
    inbox = build_approval_inbox(session_id=session_id)
    if not inbox.ok:
        return None
    for item in inbox.items:
        if str(item.get("inbox_id") or "") == inbox_id and str(item.get("lane") or "") == "workspace_terminal":
            return item
    return None


def _sessions_for_preflight(preflight_id: str) -> list[str]:
    from aethos_core.agents.runtime.subagent_session_store import list_subagent_sessions

    keys: list[str] = []
    for row in list_subagent_sessions(parent_session_id=None, limit=200):
        ids = list(row.get("terminal_preflight_ids") or [])
        if preflight_id in ids:
            key = str(row.get("session_key") or "")
            if key:
                keys.append(key)
    return keys


def execute_terminal_preflight_from_inbox(*, session_id: str, inbox_id: str) -> TerminalApprovalExecutionResult:
    item = _find_terminal_inbox_item(session_id=session_id, inbox_id=inbox_id)
    if not item:
        return TerminalApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            blockers=["inbox_item_not_found"],
            detail="Terminal preflight item not found.",
        )

    ctx = item.get("context") if isinstance(item.get("context"), dict) else {}
    preflight_id = str(ctx.get("preflight_id") or "")
    if not preflight_id:
        return TerminalApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            blockers=["preflight_id_missing"],
        )

    from aethos_core.workspace_runtime.terminal.terminal_executor import execute_terminal_command
    from aethos_core.workspace_runtime.terminal.terminal_preflight_store import (
        approve_terminal_preflight,
        get_terminal_preflight,
    )

    preflight = get_terminal_preflight(preflight_id)
    if not preflight:
        return TerminalApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            preflight_id=preflight_id,
            blockers=["preflight_not_found"],
        )

    if str(preflight.get("status") or "") == "policy_denied":
        return TerminalApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            preflight_id=preflight_id,
            blockers=["policy_denied"],
            detail=str((preflight.get("policy") or {}).get("reason") or "Policy denied"),
        )

    if preflight.get("executed_at"):
        return TerminalApprovalExecutionResult(
            ok=True,
            session_id=session_id,
            inbox_id=inbox_id,
            preflight_id=preflight_id,
            execution_status="already_executed",
            output=str(preflight.get("execution_output") or ""),
            detail="Preflight already executed.",
        )

    approve_terminal_preflight(preflight_id)
    execution = execute_terminal_command(preflight=preflight, approved=True)
    status = str(execution.get("status") or "")
    output = str(execution.get("output") or "")
    exit_code = execution.get("exit_code")

    preflight = get_terminal_preflight(preflight_id) or preflight
    preflight["executed_at"] = preflight.get("executed_at") or __import__("time").time()
    preflight["execution_status"] = status
    preflight["execution_output"] = output[:8000]
    preflight["execution_id"] = execution.get("execution_id")
    from aethos_core.workspace_runtime.terminal.terminal_preflight_store import save_terminal_preflight

    save_terminal_preflight(preflight_id, preflight)

    session_keys = _sessions_for_preflight(preflight_id)
    agent_results: list[dict[str, Any]] = []
    if session_keys and output:
        from aethos_core.agents.runtime.subagent_ops import send_subagent_message

        follow_up = (
            f"Terminal command completed (preflight `{preflight_id}`).\n\n"
            f"**Command:** `{preflight.get('command') or ''}`\n"
            f"**Exit code:** {exit_code}\n\n"
            f"```\n{output[:6000]}\n```\n\n"
            "Summarize findings and recommend next governed steps."
        )
        for key in session_keys[:3]:
            sent = send_subagent_message(
                message=follow_up,
                session_id=session_id,
                session_key=key,
            )
            agent_results.append({"session_key": key, "ok": bool(sent.get("ok")), "error": sent.get("error")})

    ok = status == "executed" and bool(execution.get("ok"))
    audit = persist_ui_approval_audit(
        {
            "session_id": session_id,
            "inbox_id": inbox_id,
            "lane": "workspace_terminal",
            "gate_id": "terminal_execute",
            "outcome": "success" if ok else "failed",
            "gate_satisfied": ok,
            "mutation_performed": ok,
            "direct_provider_mutation": False,
            "terminal_preflight_id": preflight_id,
            "execution_status": status,
            "subagent_session_keys": session_keys,
            "reply_excerpt": output[:500],
            "blockers": [] if ok else [status or "execution_failed"],
            "failure_reason": "" if ok else status,
        }
    )

    return TerminalApprovalExecutionResult(
        ok=ok,
        session_id=session_id,
        inbox_id=inbox_id,
        preflight_id=preflight_id,
        execution_status=status,
        output=output,
        exit_code=exit_code if isinstance(exit_code, int) else None,
        subagent_session_keys=session_keys,
        agent_send_results=agent_results,
        audit_id=str(audit.get("approval_id") or ""),
        detail="Terminal executed; output forwarded to linked subagent sessions."
        if agent_results
        else "Terminal executed.",
        blockers=[] if ok else [status or "execution_failed"],
    )
