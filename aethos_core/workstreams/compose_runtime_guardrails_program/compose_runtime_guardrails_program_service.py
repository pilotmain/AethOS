# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E4 / FIX 346 — compose runtime guardrails service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_346_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guard import (
    build_compose_cost_classification_report,
    build_runtime_mode_registry,
    get_runtime_mode,
    list_heavy_compose_executions,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_contract import (
    AUTHORITY_EXPANSION_FIX_346,
    COMPOSE_RUNTIME_GUARDRAILS_PHASES,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_FIX,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ID,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_INVARIANT,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_SCHEMA_VERSION,
    CORE_PRINCIPLE,
    EVIDENCE_REDUCTION_FIX_346,
    EXECUTION_PERFORMED_FIX_346,
    EXECUTIVE_FIX_MODULES,
    FORBIDDEN_GUARDRAIL_ACTIONS,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_346,
    GOVERNANCE_MUTATION_PERFORMED_FIX_346,
    LOCAL_RUNTIME_GUARDRAIL_EXECUTABLE_FIX_346,
    MUTATION_PERFORMED_FIX_346,
    PROGRAM_NON_GOALS,
    TRUST_MUTATION_AUTHORITY_FIX_346,
    TRUTH_MUTATION_FIX_346,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_executor import (
    build_benchmark_command_registry,
    build_heavy_compose_guard_report,
    build_interactive_runtime_safety_report,
    build_runtime_timeout_policy_report,
    build_test_runtime_safety_report,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_store import (
    has_runtime_guardrail_review_approve,
    list_compose_runtime_guardrails_records,
)


@dataclass(frozen=True)
class ComposeRuntimeGuardrailsProgramResult:
    ok: bool
    session_id: str
    compose_runtime_guardrails_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("session_id") or session_id) == session_id]


def _build_phase_8_runtime_safety_dashboard(*, session_id: str) -> dict[str, Any]:
    guard = build_heavy_compose_guard_report(session_id=session_id)
    executions = list_heavy_compose_executions(session_id=session_id)
    module_assessments = {
        fix_label: {"runtime_guardrails_representable": True, "compose_available": True}
        for fix_label in EXECUTIVE_FIX_MODULES
    }
    return {
        "runtime_safety_dashboard": {
            "dashboard_id": "runtime-safety-dashboard",
            "active_mode": get_runtime_mode(session_id=session_id),
            "guarded_modules": guard.get("guarded_modules"),
            "recent_heavy_executions": executions[-10:],
            "module_assessments": module_assessments,
            "evidence_reduction_performed": False,
            "read_only": True,
        }
    }


def _build_phase_9_human_review(*, session_id: str) -> dict[str, Any]:
    records = _session_records(list_compose_runtime_guardrails_records(), session_id=session_id)
    notes = [r for r in records if str(r.get("kind") or "") == "runtime_guardrail_note"]
    decisions = [r for r in records if str(r.get("kind") or "").startswith("runtime_guardrail_review_")]
    return {
        "runtime_guardrail_review_registry": {
            "registry_id": "runtime-guardrail-review-registry",
            "note_count": len(notes),
            "decision_count": len(decisions),
            "notes": notes[-10:],
            "decisions": decisions[-5:],
            "read_only": True,
        }
    }


def _success_criteria(*, session_id: str) -> dict[str, Any]:
    guard = build_heavy_compose_guard_report(session_id=session_id)
    test_safety = build_test_runtime_safety_report(session_id=session_id)
    interactive = build_interactive_runtime_safety_report(session_id=session_id)
    benchmark_cmds = build_benchmark_command_registry(session_id=session_id)

    return {
        "runtime_modes_defined": bool(build_runtime_mode_registry(session_id=session_id).get("supported_modes")),
        "critical_compose_guarded": bool(guard.get("guarded_modules")),
        "test_runtime_safety_enforced": test_safety.get("critical_compose_blocked_in_test_mode") is True,
        "interactive_defaults_operator_mode": interactive.get("chat_default_mode") == "operator",
        "benchmark_commands_separated": benchmark_cmds.get("command_count", 0) >= 3,
        "evidence_reduction_performed": False,
        "governance_unchanged": True,
        "program_complete": has_runtime_guardrail_review_approve(session_id=session_id),
    }


def build_compose_runtime_guardrails_program(*, session_id: str = "default") -> ComposeRuntimeGuardrailsProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    blockers: list[str] = []

    sections: dict[str, list[dict[str, Any]]] = {}
    phase_builders = (
        lambda session_id=sid: {"runtime_mode_registry": build_runtime_mode_registry(session_id=session_id)},
        lambda session_id=sid: {
            "compose_cost_classification_report": build_compose_cost_classification_report(session_id=session_id)
        },
        lambda session_id=sid: {"heavy_compose_guard_report": build_heavy_compose_guard_report(session_id=session_id)},
        lambda session_id=sid: {"test_runtime_safety_report": build_test_runtime_safety_report(session_id=session_id)},
        lambda session_id=sid: {
            "interactive_runtime_safety_report": build_interactive_runtime_safety_report(session_id=session_id)
        },
        lambda session_id=sid: {"benchmark_command_registry": build_benchmark_command_registry(session_id=session_id)},
        lambda session_id=sid: {"runtime_timeout_policy": build_runtime_timeout_policy_report(session_id=session_id)},
        _build_phase_8_runtime_safety_dashboard,
        _build_phase_9_human_review,
    )
    for phase, builder in zip(COMPOSE_RUNTIME_GUARDRAILS_PHASES, phase_builders, strict=True):
        sections[phase] = [builder(session_id=sid)]

    success = _success_criteria(session_id=sid)
    if not has_runtime_guardrail_review_approve(session_id=sid):
        blockers.append("runtime_guardrail_review_approve_required")

    board: dict[str, Any] = {
        "schema_version": COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_SCHEMA_VERSION,
        "workstream_id": COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ID,
        "fix_id": COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_346,
        "execution_performed": EXECUTION_PERFORMED_FIX_346,
        "core_principle": CORE_PRINCIPLE,
        "invariant": COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_INVARIANT,
        "forbidden_actions": [f"{key}: {value}" for key, value in FORBIDDEN_GUARDRAIL_ACTIONS],
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(COMPOSE_RUNTIME_GUARDRAILS_PHASES),
        "evidence_reduction": EVIDENCE_REDUCTION_FIX_346,
        "truth_mutation": TRUTH_MUTATION_FIX_346,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_346,
        "authority_expansion": AUTHORITY_EXPANSION_FIX_346,
        "governance_bypass_authority": GOVERNANCE_BYPASS_AUTHORITY_FIX_346,
        "local_runtime_guardrail_executable": LOCAL_RUNTIME_GUARDRAIL_EXECUTABLE_FIX_346,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_346,
        "active_runtime_mode": get_runtime_mode(session_id=sid),
        "success_criteria": success,
        "composed_from_workstream_e3_and_fix_345_guardrail_requirements": True,
        "sections": sections,
        "fix_346_certification_requirements": list(FIX_346_CERTIFICATION_REQUIREMENTS),
    }

    detail = (
        "Compose runtime guardrails program complete"
        if success.get("program_complete")
        else "Compose runtime guardrails composed — human review pending"
    )
    return ComposeRuntimeGuardrailsProgramResult(
        ok=True,
        session_id=sid,
        compose_runtime_guardrails_program=board,
        blockers=blockers,
        detail=detail,
    )
