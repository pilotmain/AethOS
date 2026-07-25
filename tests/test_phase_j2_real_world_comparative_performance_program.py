# SPDX-License-Identifier: Apache-2.0
"""PHASE_J2 — real-world comparative performance program tests."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store import (
    clear_governed_deployment_execution_records_for_tests,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store import (
    clear_governed_end_to_end_delivery_certification_records_for_tests,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    clear_governed_git_delivery_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_executor import (
    run_customer_delivery_pilot,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_intent import (
    handle_first_customer_delivery_pilot_intent,
    parse_first_customer_delivery_pilot_intent,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    clear_first_customer_delivery_pilot_records_for_tests,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_contract import (
    AUTHORITY_EXPANSION_FIX_365,
    BENCHMARK_MIN_SIZE,
    COMPARISON_LEVELS,
    COMPETITIVE_ACTIONS_FIX_365,
    COMPETITIVE_AUTHORITY_FIX_365,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PHASES,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID,
    STRATEGY_MUTATION_FIX_365,
    TRUST_PROMOTION_FIX_365,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_intent import (
    handle_comparative_performance_intent,
    parse_comparative_performance_intent,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_renderer import (
    render_all_comparative_performance_deliverables,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_service import (
    build_real_world_comparative_performance_program,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_store import (
    clear_comparative_performance_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_comparative_performance_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_comparative_performance_records_for_tests()


def _seed_execution_evidence(customer_session: str = "ws-j2-alpha") -> None:
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer delivery request: goal=Health endpoint, scope=small service, type=health_check_endpoint"
        ),
        session_id=customer_session,
    )
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True


def _seed_comparative_performance(program_session: str = "ws-j2") -> None:
    _seed_execution_evidence("ws-j2-alpha")
    handle_comparative_performance_intent(
        parse_comparative_performance_intent(
            "comparative performance benchmark: benchmark_id=baseline-human, approach=human_only, category=delivery, time_to_delivery_ms=7200000"
        ),
        session_id=program_session,
    )
    handle_comparative_performance_intent(
        parse_comparative_performance_intent(
            "comparative performance review approve: Human approves real-world comparative performance evidence"
        ),
        session_id=program_session,
    )


def test_phase_phases():
    assert REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID == "PHASE_J2"
    assert len(REAL_WORLD_COMPARATIVE_PERFORMANCE_PHASES) == 9
    assert len(COMPARISON_LEVELS) == 5
    assert BENCHMARK_MIN_SIZE == 1
    assert COMPETITIVE_AUTHORITY_FIX_365 is False
    assert COMPETITIVE_ACTIONS_FIX_365 is False
    assert STRATEGY_MUTATION_FIX_365 is False
    assert AUTHORITY_EXPANSION_FIX_365 is False
    assert TRUST_PROMOTION_FIX_365 is False


def test_intent_parsing():
    assert parse_comparative_performance_intent("show comparative performance dashboard") == {
        "action": "view",
        "focus": "comparative_performance_dashboard",
    }
    benchmark = parse_comparative_performance_intent(
        "comparative performance benchmark: benchmark_id=bench-1, approach=human_only, category=delivery"
    )
    assert benchmark["action"] == "benchmark"


def test_program_phases_and_deliverables():
    _seed_comparative_performance(program_session="ws-j2-full")
    board = build_real_world_comparative_performance_program(
        session_id="ws-j2-full"
    ).real_world_comparative_performance_program
    assert board["phase_id"] == REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID
    assert board["competitive_authority"] is False
    assert board["strategy_mutation"] is False
    for phase in REAL_WORLD_COMPARATIVE_PERFORMANCE_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["benchmark_registry_demonstrated"] is True
    assert board["success_criteria"]["delivery_comparison_demonstrated"] is True
    assert board["success_criteria"]["deployment_comparison_demonstrated"] is True
    assert board["success_criteria"]["customer_outcome_comparison_demonstrated"] is True
    assert board["success_criteria"]["operational_comparison_demonstrated"] is True
    assert board["success_criteria"]["comparative_learning_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["delivery_performance_delta"] != 0 or board["metrics"]["deployment_performance_delta"] != 0

    deliverables = render_all_comparative_performance_deliverables(board)
    assert set(deliverables) == {
        "REAL_WORLD_COMPARATIVE_PERFORMANCE_REPORT.md",
        "DELIVERY_COMPARISON_ANALYSIS.md",
        "CUSTOMER_OUTCOME_COMPARISON_REPORT.md",
    }
    assert "Comparative performance ≠ competitive authority" in deliverables["REAL_WORLD_COMPARATIVE_PERFORMANCE_REPORT.md"]
