# SPDX-License-Identifier: Apache-2.0
"""
Governed Cursor / terminal jobs for developer agent — mutation-gated pattern.

Creates terminal preflight records (pending approval). Never auto-executes.
"""

from __future__ import annotations

from time import time
from typing import Any
from uuid import uuid4

from aethos_core.workspace_runtime.terminal.terminal_preflight import run_terminal_preflight

PROVIDER_EXEC_PROVIDERS = frozenset(
    {"railway", "vercel", "supabase", "stripe", "resend", "redis", "github", "shell"}
)


def create_governed_terminal_preflight(
    *,
    command: str,
    session_id: str = "default",
    workspace_hint: str | None = None,
    workspace_id: str | None = None,
    cwd: str | None = None,
    subagent_session_key: str | None = None,
    job_kind: str = "terminal",
) -> dict[str, Any]:
    raw_cmd = (command or "").strip()
    if not raw_cmd:
        return {"ok": False, "error": "command_required"}

    preflight = run_terminal_preflight(
        command=raw_cmd,
        workspace_id=workspace_id,
        workspace_hint=workspace_hint,
        cwd=cwd,
    )
    preflight_id = str(preflight.get("preflight_id") or "")
    if subagent_session_key and preflight_id:
        from aethos_core.agents.runtime.subagent_session_store import link_terminal_preflight

        link_terminal_preflight(subagent_session_key, preflight_id)

    return {
        "ok": bool(preflight.get("ok")),
        "preflight_id": preflight_id,
        "status": preflight.get("status"),
        "command": preflight.get("command") or raw_cmd,
        "cwd": preflight.get("cwd"),
        "approval_required": True,
        "execution_enabled": False,
        "autonomous_execution_blocked": True,
        "subagent_session_key": subagent_session_key,
        "session_id": session_id,
        "job_kind": job_kind,
        "policy": preflight.get("policy"),
        "mission_control_hint": "Mission Control → Workspace Operations → approve terminal preflight, then POST /workspace/terminal/execute",
        "detail": preflight.get("reason") or preflight.get("error"),
        "preflight": preflight,
    }


def create_provider_exec_preflight(
    *,
    provider: str,
    command: str,
    purpose: str = "",
    session_id: str = "default",
    workspace_hint: str | None = None,
    workspace_id: str | None = None,
    cwd: str | None = None,
) -> dict[str, Any]:
    """Governed credentialed execution (handoff §1/§3).

    Read-only commands run immediately (sandboxed + audited); mutating commands
    create a Mission Control preflight that must be approved before execution.
    Credentials are resolved from the vault at execution time only — never echoed.
    """
    from aethos_core.credentials.provider_alias_resolution import build_provider_cli_env
    from aethos_core.workspace_runtime.terminal.terminal_executor import execute_provider_command
    from aethos_core.workspace_runtime.terminal.terminal_preflight_store import save_terminal_preflight
    from aethos_core.workspace_runtime.workspace_policy import evaluate_provider_exec_policy

    raw_cmd = (command or "").strip()
    if not raw_cmd:
        return {"ok": False, "error": "command_required"}
    prov = (provider or "shell").strip().lower()
    if prov not in PROVIDER_EXEC_PROVIDERS:
        return {
            "ok": False,
            "error": "unknown_provider",
            "detail": f"provider must be one of: {', '.join(sorted(PROVIDER_EXEC_PROVIDERS))}",
        }

    policy = evaluate_provider_exec_policy(raw_cmd)
    if not policy.get("allowed"):
        return {
            "ok": False,
            "error": policy.get("error") or "policy_denied",
            "detail": policy.get("reason"),
            "policy": policy,
        }

    # Missing credential → precise vault prompt; never ask for the secret in chat.
    injection = build_provider_cli_env(prov)
    if injection.get("missing"):
        return {
            "ok": False,
            "error": "credential_required",
            "provider": prov,
            "detail": injection.get("detail") or f"Needs a {prov} token in the Mission Control vault.",
        }

    resolved_cwd = _resolve_provider_cwd(cwd=cwd, workspace_id=workspace_id, workspace_hint=workspace_hint)
    read_only = bool(policy.get("read_only"))
    preflight_id = f"pex-{uuid4().hex[:12]}"
    record = {
        "ok": True,
        "preflight_id": preflight_id,
        "provider_exec": True,
        "provider": prov,
        "purpose": (purpose or "").strip(),
        "command": raw_cmd,
        "cwd": resolved_cwd,
        "workspace_id": workspace_id,
        "session_id": session_id,
        "read_only": read_only,
        "status": "pending_approval" if not read_only else "auto_approved_readonly",
        "approval_required": not read_only,
        "execution_enabled": read_only,
        "autonomous_execution_blocked": not read_only,
        "policy": policy,
        "created_at": time(),
        "injected_env_names": sorted((injection.get("env") or {}).keys()),
    }
    save_terminal_preflight(preflight_id, record)

    if read_only:
        # Investigation is fast: run now, sandboxed + audited, output redacted.
        execution = execute_provider_command(preflight=record, approved=True)
        return {
            "ok": bool(execution.get("ok")),
            "preflight_id": preflight_id,
            "provider": prov,
            "purpose": record["purpose"],
            "command": raw_cmd,
            "read_only": True,
            "tier": "read_only_auto_run",
            "status": execution.get("status"),
            "output": execution.get("output"),
            "exit_code": execution.get("exit_code"),
            "artifact_id": execution.get("artifact_id"),
            "audit_id": execution.get("audit_id"),
            "injected_env_names": execution.get("injected_env_names"),
        }

    return {
        "ok": True,
        "preflight_id": preflight_id,
        "provider": prov,
        "purpose": record["purpose"],
        "command": raw_cmd,
        "read_only": False,
        "tier": "mutating_requires_approval",
        "status": "pending_approval",
        "approval_required": True,
        "execution_enabled": False,
        "autonomous_execution_blocked": True,
        "blast_radius": _blast_radius(prov, policy),
        "mission_control_hint": "Approve in Mission Control → Workspace Operations, then it executes with vault creds.",
        "injected_env_names": record["injected_env_names"],
    }


def _resolve_provider_cwd(
    *, cwd: str | None, workspace_id: str | None, workspace_hint: str | None
) -> str | None:
    if cwd:
        return cwd
    try:
        from aethos_core.workspace_runtime.workspace_registry import resolve_workspace

        row = resolve_workspace(workspace_id, workspace_hint)
        if row:
            return str(row.get("path"))
    except Exception:
        pass
    try:
        from aethos_core.local_workspace.readonly.actions import _repo_from_hint

        return str(_repo_from_hint(workspace_hint or "aethos", session_id="default"))
    except Exception:
        return None


def _blast_radius(provider: str, policy: dict[str, Any]) -> str:
    binary = str(policy.get("binary") or provider)
    return f"Runs `{binary}` against your {provider} account with vault credentials. Side effects possible."


def propose_cursor_workspace_open(
    *,
    workspace_hint: str | None = None,
    path: str | None = None,
    subagent_session_key: str | None = None,
    session_id: str = "default",
) -> dict[str, Any]:
    """Proposal to open workspace in Cursor — requires terminal preflight approval."""
    from aethos_core.workspace_runtime.app_adapters import open_in_application

    proposal = open_in_application(app="cursor", path=path, workspace_hint=workspace_hint)
    if proposal.get("error") == "cursor_cli_not_found":
        return {
            "ok": False,
            "error": "cursor_cli_not_found",
            "proposal": proposal.get("proposal"),
            "hint": "Install Cursor CLI or open the repo manually.",
        }
    command_parts = proposal.get("command_proposal") or []
    if not command_parts:
        return {"ok": False, "error": "cursor_command_unavailable", "proposal": proposal}
    command = " ".join(str(p) for p in command_parts)
    out = create_governed_terminal_preflight(
        command=command,
        session_id=session_id,
        workspace_hint=workspace_hint,
        subagent_session_key=subagent_session_key,
        job_kind="cursor_open",
    )
    out["cursor_proposal"] = proposal
    return out
