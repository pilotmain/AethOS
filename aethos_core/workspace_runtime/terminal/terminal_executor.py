# SPDX-License-Identifier: Apache-2.0
"""Terminal executor — bounded approved command execution."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.workspace_runtime.workspace_artifacts import store_workspace_runtime_artifact
from aethos_core.workspace_runtime.workspace_audit import record_workspace_audit
from aethos_core.workspace_runtime.workspace_memory import record_workspace_context
from aethos_core.workspace_runtime.workspace_policy import evaluate_command_policy


MAX_OUTPUT = 8000
DEFAULT_TIMEOUT = 60.0
PROVIDER_EXEC_TIMEOUT = 180.0

# Providers whose work can fall back to their HTTP API via curl when the CLI is
# not installed (handoff §6 — be honest, never pretend).
_CURL_FALLBACK_PROVIDERS = {"supabase", "stripe", "resend"}


def execute_terminal_command(
    *,
    preflight: dict[str, Any],
    approved: bool = False,
    timeout_sec: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    # Credentialed provider execution lane (handoff §1/§2) — vault creds injected
    # at runtime, output redacted. Routed here so MC approval → execute reuses the
    # same governed path as ordinary terminal jobs.
    if preflight.get("provider_exec"):
        return execute_provider_command(preflight=preflight, approved=approved)
    if not approved:
        return {
            "ok": False,
            "status": "approval_required",
            "error": "Terminal execution requires explicit approval.",
            "execution_enabled": False,
        }

    command = str(preflight.get("command") or "")
    policy = evaluate_command_policy(command)
    if not policy.get("allowed"):
        art = store_workspace_runtime_artifact(
            artifact_type="workspace_policy_denial",
            workspace_id=preflight.get("workspace_id"),
            session_id=preflight.get("session_id"),
            payload={"command": command, "policy": policy},
            summary="Execution blocked by policy",
        )
        return {"ok": False, "status": "policy_denied", "artifact_id": art.get("artifact_id"), "policy": policy}

    cwd = preflight.get("cwd")
    if not cwd or not Path(str(cwd)).is_dir():
        return {"ok": False, "status": "invalid_cwd", "error": "Workspace path not found."}

    execution_id = f"tex-{uuid4().hex[:12]}"
    try:
        result = _run_bounded(command, cwd=Path(str(cwd)), timeout_sec=timeout_sec)
    except subprocess.TimeoutExpired:
        result = {"ok": False, "exit_code": -1, "output": "Command timed out.", "timed_out": True}

    artifact = store_workspace_runtime_artifact(
        artifact_type="workspace_terminal_output",
        workspace_id=preflight.get("workspace_id"),
        session_id=preflight.get("session_id"),
        payload={
            "execution_id": execution_id,
            "command": command,
            "cwd": cwd,
            "result": result,
            "preflight_id": preflight.get("preflight_id"),
        },
        summary=f"Terminal: {command[:80]}",
    )
    audit_id = f"waudit-{uuid4().hex[:12]}"
    record_workspace_audit(
        {
            "audit_id": audit_id,
            "action": "terminal_execute",
            "execution_id": execution_id,
            "preflight_id": preflight.get("preflight_id"),
            "command": command,
            "artifact_id": artifact.get("artifact_id"),
            "ok": result.get("ok"),
        }
    )
    record_workspace_context(
        workspace_id=preflight.get("workspace_id"),
        repo_path=str(cwd),
        command=command,
        replay_id=artifact.get("artifact_id"),
    )
    return {
        "ok": bool(result.get("ok")),
        "execution_id": execution_id,
        "status": "executed" if result.get("ok") else "execution_failed",
        "artifact_id": artifact.get("artifact_id"),
        "audit_id": audit_id,
        "output": result.get("output"),
        "exit_code": result.get("exit_code"),
        "merge_enabled": False,
        "autonomous_execution_blocked": True,
    }


def _run_bounded(command: str, *, cwd: Path, timeout_sec: float) -> dict[str, Any]:
    lower = command.lower().strip()
    if lower.startswith("git "):
        args = shlex.split(command)
        return _run_subprocess(args, cwd=cwd, timeout_sec=timeout_sec)
    if lower.startswith("pytest") or lower.startswith("python -m pytest"):
        args = shlex.split(command)
        return _run_subprocess(args, cwd=cwd, timeout_sec=min(timeout_sec, 90.0))
    if lower.startswith("npm "):
        args = shlex.split(command)
        if len(args) >= 2 and args[1] in ("test", "run"):
            return _run_subprocess(args, cwd=cwd, timeout_sec=min(timeout_sec, 120.0))
        raise PermissionError("npm command not allowlisted")
    if lower.startswith("cursor "):
        args = shlex.split(command)
        return _run_subprocess(args, cwd=cwd, timeout_sec=min(timeout_sec, 20.0))
    if lower in ("pwd", "ls") or lower.startswith("ls "):
        args = shlex.split(command)
        return _run_subprocess(args, cwd=cwd, timeout_sec=10.0)
    raise PermissionError("Command not allowlisted for execution")


def _run_subprocess(args: list[str], *, cwd: Path, timeout_sec: float) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if len(out) > MAX_OUTPUT:
        out = out[: MAX_OUTPUT - 40] + "\n… (truncated)"
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "output": out,
        "runner": args[0],
    }


def execute_provider_command(
    *,
    preflight: dict[str, Any],
    approved: bool = False,
    timeout_sec: float = PROVIDER_EXEC_TIMEOUT,
) -> dict[str, Any]:
    """Execute a credentialed provider CLI/API command (handoff §1/§2/§5/§6).

    Read-only commands may arrive pre-approved (auto-run); mutating commands require
    explicit approval. Vault credentials are injected as process env at execution
    time only; captured output is redacted of all injected secrets before return.
    """
    from aethos_core.credentials.provider_alias_resolution import build_provider_cli_env
    from aethos_core.security.secret_redaction import redact_known_secrets
    from aethos_core.workspace_runtime.workspace_policy import evaluate_provider_exec_policy

    command = str(preflight.get("command") or "")
    provider = str(preflight.get("provider") or "shell").strip().lower()

    policy = evaluate_provider_exec_policy(command)
    if not policy.get("allowed"):
        return {"ok": False, "status": "policy_denied", "policy": policy, "error": policy.get("reason")}

    # Mutating commands must be approved; read-only may auto-run (still sandboxed).
    if policy.get("approval_required") and not approved:
        return {
            "ok": False,
            "status": "approval_required",
            "error": "Mutating provider command requires Mission Control approval.",
            "execution_enabled": False,
        }

    binary = str(policy.get("binary") or "")
    if binary and shutil.which(binary) is None:
        # §6 — honest about a missing CLI; never pretend it ran.
        if provider in _CURL_FALLBACK_PROVIDERS or binary in _CURL_FALLBACK_PROVIDERS:
            detail = (
                f"The `{binary}` CLI is not installed. Use the {provider} HTTP API via "
                f"`curl` with the injected token instead, or install the `{binary}` CLI."
            )
        else:
            detail = f"The `{binary}` CLI is not installed. Install it to run this command."
        return {"ok": False, "status": "cli_not_installed", "binary": binary, "error": detail, "detail": detail}

    injection = build_provider_cli_env(provider)
    if injection.get("missing"):
        return {
            "ok": False,
            "status": "credential_required",
            "provider": provider,
            "error": injection.get("detail") or f"Needs a {provider} token in the Mission Control vault.",
            "detail": injection.get("detail"),
        }

    cwd = preflight.get("cwd")
    if not cwd or not Path(str(cwd)).is_dir():
        cwd = _default_provider_cwd()

    secrets = list(injection.get("secrets") or [])
    env_overlay = dict(injection.get("env") or {})
    execution_id = f"pex-{uuid4().hex[:12]}"
    try:
        result = _run_credentialed(command, cwd=Path(str(cwd)), env_overlay=env_overlay, timeout_sec=timeout_sec)
    except subprocess.TimeoutExpired:
        result = {"ok": False, "exit_code": -1, "output": "Command timed out.", "timed_out": True}
    except FileNotFoundError as exc:
        result = {"ok": False, "exit_code": -1, "output": f"Binary not found: {exc}"}

    # Redact any injected secret that leaked into output before it leaves this layer.
    result["output"] = redact_known_secrets(str(result.get("output") or ""), secrets)

    artifact = store_workspace_runtime_artifact(
        artifact_type="provider_exec_output",
        workspace_id=preflight.get("workspace_id"),
        session_id=preflight.get("session_id"),
        payload={
            "execution_id": execution_id,
            "provider": provider,
            "command": command,
            "purpose": preflight.get("purpose"),
            "cwd": str(cwd),
            "read_only": bool(policy.get("read_only")),
            "result": result,
            "preflight_id": preflight.get("preflight_id"),
        },
        summary=f"provider_exec[{provider}]: {command[:72]}",
    )
    audit_id = f"waudit-{uuid4().hex[:12]}"
    record_workspace_audit(
        {
            "audit_id": audit_id,
            "action": "provider_exec",
            "provider": provider,
            "read_only": bool(policy.get("read_only")),
            "execution_id": execution_id,
            "preflight_id": preflight.get("preflight_id"),
            "command": command,
            "purpose": preflight.get("purpose"),
            "artifact_id": artifact.get("artifact_id"),
            "ok": result.get("ok"),
        }
    )
    return {
        "ok": bool(result.get("ok")),
        "execution_id": execution_id,
        "provider": provider,
        "read_only": bool(policy.get("read_only")),
        "status": "executed" if result.get("ok") else "execution_failed",
        "artifact_id": artifact.get("artifact_id"),
        "audit_id": audit_id,
        "output": result.get("output"),
        "exit_code": result.get("exit_code"),
        "injected_env_names": sorted(env_overlay.keys()),
        "autonomous_execution_blocked": bool(policy.get("approval_required")),
    }


def _default_provider_cwd() -> str:
    try:
        from aethos_core.local_workspace.readonly.actions import _repo_from_hint

        return str(_repo_from_hint("aethos", session_id="default"))
    except Exception:
        return str(Path.cwd())


def _run_credentialed(
    command: str,
    *,
    cwd: Path,
    env_overlay: dict[str, str],
    timeout_sec: float,
) -> dict[str, Any]:
    """Run an allowlisted provider command with vault env injected, output-bounded.

    Never uses a shell; tokens are passed via env only (never on the command line).
    """
    args = shlex.split(command)
    if not args:
        return {"ok": False, "exit_code": -1, "output": "Empty command."}
    env = dict(os.environ)
    env.update(env_overlay)
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        env=env,
        check=False,
    )
    out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if len(out) > MAX_OUTPUT:
        out = out[: MAX_OUTPUT - 40] + "\n… (truncated)"
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "output": out,
        "runner": args[0],
    }
