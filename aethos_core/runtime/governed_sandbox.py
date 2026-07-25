# SPDX-License-Identifier: Apache-2.0
"""Governed sandbox runtime — non-main session isolation with AethOS preflight gates."""

from __future__ import annotations

from typing import Any


def sandbox_runtime_status() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    enabled = bool(getattr(settings, "host_executor_enabled", False))
    return {
        "ok": True,
        "sandbox_lane_enabled": enabled,
        "host_executor_enabled": enabled,
        "policy": "preflight_only",
        "hint": "Sandbox runs require terminal_create_preflight + Mission Control approval.",
        "allowed_readonly_probes": [
            "python -m pytest tests/test_health.py -q --co",
            "aethos doctor --json",
        ],
    }


def propose_sandbox_probe(*, command: str, session_id: str = "operator") -> dict[str, Any]:
    cmd = (command or "").strip()
    if not cmd:
        return {"ok": False, "error": "command_required"}
    status = sandbox_runtime_status()
    if not status.get("host_executor_enabled"):
        return {"ok": False, "error": "host_executor_disabled", "hint": "Set HOST_EXECUTOR_ENABLED=true"}
    allowed = list(status.get("allowed_readonly_probes") or [])
    if cmd not in allowed:
        return {
            "ok": False,
            "error": "command_not_allowlisted",
            "allowed_readonly_probes": allowed,
        }
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    raw = execute_agent_tool(
        "terminal_create_preflight",
        {"command": cmd, "rationale": "Governed sandbox probe"},
        session_id=session_id,
    )
    import json

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {"ok": False, "error": "preflight_failed"}
    return {"ok": bool(payload.get("ok")), "preflight": payload, "command": cmd}
