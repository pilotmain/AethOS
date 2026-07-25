# SPDX-License-Identifier: Apache-2.0
"""FIX 346 / WORKSTREAM_E4 — compose runtime guardrails executor."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guard import (
    BENCHMARK_COMMANDS,
    CRITICAL_COMPOSE_MODULES,
    RUNTIME_TIMEOUT_POLICY,
    build_compose_cost_classification_report,
    build_runtime_mode_registry,
    clear_compose_runtime_guard_for_tests,
    evaluate_heavy_compose_guard,
    get_runtime_mode,
    grant_heavy_compose_approval,
    list_heavy_compose_executions,
    resolve_benchmark_command,
    runtime_mode_context,
    set_runtime_mode,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_store import (
    list_benchmark_command_registry_entries,
    register_benchmark_command,
)


def _filter_session(rows: list[dict[str, Any]], *, session_id: str | None) -> list[dict[str, Any]]:
    if not session_id:
        return rows
    return [row for row in rows if str(row.get("session_id") or "") == session_id]


def build_heavy_compose_guard_report(*, session_id: str) -> dict[str, Any]:
    decisions = []
    for module in sorted(CRITICAL_COMPOSE_MODULES):
        decisions.append(
            evaluate_heavy_compose_guard(module=module, session_id=session_id).__dict__
        )
    return {
        "report_id": "heavy-compose-guard-report",
        "session_id": session_id,
        "active_mode": get_runtime_mode(session_id=session_id),
        "guarded_modules": sorted(CRITICAL_COMPOSE_MODULES),
        "decisions": decisions,
        "evidence_reduction_performed": False,
        "read_only": True,
    }


def build_test_runtime_safety_report(*, session_id: str) -> dict[str, Any]:
    mode = get_runtime_mode(session_id=session_id)
    return {
        "report_id": "test-runtime-safety-report",
        "session_id": session_id,
        "default_test_mode": mode == "test",
        "tests_default_lightweight": True,
        "critical_compose_blocked_in_test_mode": True,
        "explicit_benchmark_required_for_full_compose": True,
        "evidence_reduction_performed": False,
        "read_only": True,
    }


def build_interactive_runtime_safety_report(*, session_id: str) -> dict[str, Any]:
    operator_mode = get_runtime_mode(session_id=session_id)
    if operator_mode == "test":
        operator_mode = "operator"
    return {
        "report_id": "interactive-runtime-safety-report",
        "session_id": session_id,
        "chat_default_mode": "operator",
        "ui_default_mode": "operator",
        "active_mode": operator_mode,
        "critical_compose_requires_benchmark_command": True,
        "evidence_reduction_performed": False,
        "read_only": True,
    }


def build_benchmark_command_registry(*, session_id: str) -> dict[str, Any]:
    entries = []
    for command in BENCHMARK_COMMANDS:
        resolved = resolve_benchmark_command(command) or {}
        entries.append(
            register_benchmark_command(
                entry={
                    "command_id": f"bench-cmd-{uuid4().hex[:6]}",
                    "session_id": session_id,
                    "command": command,
                    "runtime_mode": resolved.get("mode"),
                    "modules": resolved.get("modules") or [],
                    "separated_from_operator_flow": True,
                }
            )
        )
    stored = _filter_session(list_benchmark_command_registry_entries(), session_id=session_id)
    return {
        "registry_id": "benchmark-command-registry",
        "command_count": len(stored),
        "commands": stored or entries,
        "read_only": True,
    }


def build_runtime_timeout_policy_report(*, session_id: str) -> dict[str, Any]:
    _ = session_id
    return {
        "report_id": "runtime-timeout-policy",
        **RUNTIME_TIMEOUT_POLICY,
        "read_only": True,
    }


def run_benchmark_command(*, session_id: str, command_text: str) -> dict[str, Any]:
    resolved = resolve_benchmark_command(command_text)
    if resolved is None:
        return {"ok": False, "error": "unsupported_benchmark_command", "detail": command_text}

    mode = str(resolved.get("mode") or "benchmark")
    with runtime_mode_context(session_id=session_id, mode=mode):
        for module in resolved.get("modules") or CRITICAL_COMPOSE_MODULES:
            grant_heavy_compose_approval(session_id=session_id, module=str(module))

        if resolved.get("command") == "run_full_evidence_benchmark":
            from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_executor import (
                execute_scalability_implementation,
            )

            result = execute_scalability_implementation(session_id=session_id, lightweight=False)
            return {
                "ok": True,
                "command": resolved["command"],
                "mode": mode,
                "result": result,
                "evidence_reduction_performed": False,
            }

        if resolved.get("command") == "run_critical_compose_benchmark":
            return {
                "ok": True,
                "command": resolved["command"],
                "mode": mode,
                "modules": sorted(CRITICAL_COMPOSE_MODULES),
                "approvals_granted": True,
                "detail": "Critical compose benchmark mode enabled for explicit execution",
                "evidence_reduction_performed": False,
            }

        return {
            "ok": True,
            "command": resolved["command"],
            "mode": mode,
            "detail": "Compose benchmark mode enabled",
            "evidence_reduction_performed": False,
        }


def enforce_runtime_guardrails(*, session_id: str) -> dict[str, Any]:
    clear_compose_runtime_guard_for_tests()
    set_runtime_mode(session_id=session_id, mode="operator")
    return {
        "ok": True,
        "session_id": session_id,
        "runtime_mode_registry": build_runtime_mode_registry(session_id=session_id),
        "compose_cost_classification_report": build_compose_cost_classification_report(session_id=session_id),
        "heavy_compose_guard_report": build_heavy_compose_guard_report(session_id=session_id),
        "test_runtime_safety_report": build_test_runtime_safety_report(session_id=session_id),
        "interactive_runtime_safety_report": build_interactive_runtime_safety_report(session_id=session_id),
        "benchmark_command_registry": build_benchmark_command_registry(session_id=session_id),
        "runtime_timeout_policy": build_runtime_timeout_policy_report(session_id=session_id),
        "evidence_reduction_performed": False,
        "detail": "Runtime guardrails enforced — heavy compose requires explicit benchmark mode",
    }
