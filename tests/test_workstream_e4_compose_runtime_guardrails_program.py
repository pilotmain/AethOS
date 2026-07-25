# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E4 — compose runtime guardrails tests."""

from __future__ import annotations

import pytest

from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guard import (
    HeavyComposeGuardError,
    clear_compose_runtime_guard_for_tests,
    evaluate_heavy_compose_guard,
    get_runtime_mode,
    grant_heavy_compose_approval,
    runtime_mode_context,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_contract import (
    AUTHORITY_EXPANSION_FIX_346,
    COMPOSE_RUNTIME_GUARDRAILS_PHASES,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ID,
    EVIDENCE_REDUCTION_FIX_346,
    TRUTH_MUTATION_FIX_346,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_executor import (
    enforce_runtime_guardrails,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_intent import (
    handle_compose_runtime_guardrails_intent,
    parse_compose_runtime_guardrails_intent,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_renderer import (
    render_all_compose_runtime_guardrails_deliverables,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_service import (
    build_compose_runtime_guardrails_program,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_store import (
    clear_compose_runtime_guardrails_records_for_tests,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_executor import (
    execute_scalability_implementation,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_compose_runtime_guardrails_records_for_tests()
    clear_compose_runtime_guard_for_tests()
    yield
    clear_compose_runtime_guardrails_records_for_tests()
    clear_compose_runtime_guard_for_tests()


def test_workstream_phases():
    assert COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ID == "WORKSTREAM_E4"
    assert len(COMPOSE_RUNTIME_GUARDRAILS_PHASES) == 9
    assert EVIDENCE_REDUCTION_FIX_346 is False
    assert TRUTH_MUTATION_FIX_346 is False
    assert AUTHORITY_EXPANSION_FIX_346 is False


def test_runtime_mode_defaults_to_test_under_pytest():
    assert get_runtime_mode(session_id="ws-e4-mode") == "test"


def test_critical_compose_blocked_in_test_mode():
    decision = evaluate_heavy_compose_guard(module="FIX 322", session_id="ws-e4-guard")
    assert decision.allowed is False
    assert decision.reason == "heavy_compose_requires_benchmark_or_full_evidence_mode"


def test_benchmark_mode_allows_critical_compose():
    with runtime_mode_context(session_id="ws-e4-bench", mode="benchmark"):
        decision = evaluate_heavy_compose_guard(module="FIX 323", session_id="ws-e4-bench")
        assert decision.allowed is True


def test_execute_scalability_blocks_full_compose_in_test_mode():
    with pytest.raises(HeavyComposeGuardError):
        execute_scalability_implementation(session_id="ws-e4-exec-block", lightweight=False)


def test_execute_scalability_lightweight_allowed_in_test_mode():
    result = execute_scalability_implementation(session_id="ws-e4-exec-ok", lightweight=True)
    assert result["ok"] is True
    assert result["lightweight"] is True


def test_intent_parsing_and_review_flow():
    assert parse_compose_runtime_guardrails_intent("show runtime safety dashboard") == {
        "action": "view",
        "focus": "runtime_safety_dashboard",
    }
    benchmark = parse_compose_runtime_guardrails_intent("run compose benchmark")
    assert benchmark["action"] == "benchmark"
    assert benchmark["mode"] == "benchmark"

    handle_compose_runtime_guardrails_intent(
        parse_compose_runtime_guardrails_intent("runtime guardrail note: Guardrails verified"),
        session_id="ws-e4-review",
    )
    handle_compose_runtime_guardrails_intent(
        parse_compose_runtime_guardrails_intent(
            "runtime guardrail review approve: Human approves runtime guardrails"
        ),
        session_id="ws-e4-review",
    )

    board = build_compose_runtime_guardrails_program(session_id="ws-e4-review").compose_runtime_guardrails_program
    assert board["success_criteria"]["program_complete"] is True
    assert board["success_criteria"]["critical_compose_guarded"] is True
    assert board["success_criteria"]["evidence_reduction_performed"] is False

    deliverables = render_all_compose_runtime_guardrails_deliverables(board)
    assert set(deliverables) == {
        "COMPOSE_RUNTIME_GUARDRAILS_REPORT.md",
        "BENCHMARK_MODE_SEPARATION_REPORT.md",
        "TEST_RUNTIME_SAFETY_REPORT.md",
    }
    assert "Runtime guardrails ≠ evidence reduction" in deliverables["COMPOSE_RUNTIME_GUARDRAILS_REPORT.md"]


def test_enforce_runtime_guardrails():
    result = enforce_runtime_guardrails(session_id="ws-e4-enforce")
    assert result["ok"] is True
    assert result["runtime_mode_registry"]["active_mode"] == "operator"
    assert "FIX 322" in result["heavy_compose_guard_report"]["guarded_modules"]


def test_session_approval_allows_compose_in_operator_mode():
    grant_heavy_compose_approval(session_id="ws-e4-approve", module="FIX 322")
    decision = evaluate_heavy_compose_guard(module="FIX 322", session_id="ws-e4-approve")
    assert decision.allowed is True
    assert decision.reason == "session_heavy_compose_approval"
