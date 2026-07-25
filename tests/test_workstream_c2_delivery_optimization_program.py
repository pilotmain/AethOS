# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C2 — delivery optimization program tests."""

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
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_contract import (
    AUTONOMOUS_MUTATION_ENABLED_FIX_340,
    DELIVERY_OPTIMIZATION_PHASES,
    DELIVERY_OPTIMIZATION_PROGRAM_ID,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_executor import (
    run_delivery_optimization_analysis,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_intent import (
    handle_delivery_optimization_intent,
    parse_delivery_optimization_intent,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_renderer import (
    render_all_delivery_optimization_deliverables,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_service import (
    build_delivery_optimization_program,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_store import (
    clear_delivery_optimization_records_for_tests,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_executor import (
    run_delivery_proof,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_store import (
    clear_real_world_delivery_proof_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_real_world_delivery_proof_records_for_tests()
    clear_delivery_optimization_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_real_world_delivery_proof_records_for_tests()
    clear_delivery_optimization_records_for_tests()


def _seed_c1_and_analyze(session_id: str = "ws-c2") -> dict:
    run_delivery_proof(
        session_id=session_id,
        repository="aethos",
        candidate_type="documentation_update",
    )
    handle_delivery_optimization_intent(
        parse_delivery_optimization_intent("delivery optimization note: Analyze post-proof delivery signals"),
        session_id=session_id,
    )
    analysis = run_delivery_optimization_analysis(session_id=session_id)
    handle_delivery_optimization_intent(
        parse_delivery_optimization_intent(
            "delivery optimization review approve: Human approves optimization recommendations for adoption review"
        ),
        session_id=session_id,
    )
    return analysis


def test_workstream_phases():
    assert DELIVERY_OPTIMIZATION_PROGRAM_ID == "WORKSTREAM_C2"
    assert len(DELIVERY_OPTIMIZATION_PHASES) == 9


def test_intent_parsing():
    assert parse_delivery_optimization_intent("show delivery optimization dashboard") == {
        "action": "view",
        "focus": "delivery_optimization_dashboard",
    }
    assert parse_delivery_optimization_intent("analyze delivery optimization") == {"action": "analyze"}
    parsed = parse_delivery_optimization_intent(
        "delivery optimization review approve: Human approves recommendations only"
    )
    assert parsed == {
        "action": "record",
        "kind": "delivery_optimization_review_approve",
        "content": "Human approves recommendations only",
    }


def test_program_phases_and_outputs():
    board = build_delivery_optimization_program(session_id="ws-c2-empty").delivery_optimization_program
    assert board["workstream_id"] == DELIVERY_OPTIMIZATION_PROGRAM_ID
    assert board["autonomous_mutation_enabled"] is False
    assert board["authority_expansion"] is False
    for phase in DELIVERY_OPTIMIZATION_PHASES:
        assert phase in board["sections"]


def test_optimization_analysis_and_completion():
    analysis = _seed_c1_and_analyze(session_id="ws-c2-run")
    assert analysis["ok"] is True
    assert analysis["autonomous_mutation_performed"] is False
    assert analysis["improvement_opportunities"]["opportunity_count"] >= 1

    board = build_delivery_optimization_program(session_id="ws-c2-run").delivery_optimization_program
    assert board["success_criteria"]["improvement_recommendations_present"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["trends"]["deployment_success_trend"] >= 0.0


def test_deliverable_renderers():
    _seed_c1_and_analyze(session_id="ws-c2-render")
    board = build_delivery_optimization_program(session_id="ws-c2-render").delivery_optimization_program
    deliverables = render_all_delivery_optimization_deliverables(board)
    assert set(deliverables) == {
        "DELIVERY_OPTIMIZATION_REPORT.md",
        "DELIVERY_RELIABILITY_INTELLIGENCE_REPORT.md",
        "DELIVERY_IMPROVEMENT_OPPORTUNITIES.md",
    }
    assert "Delivery optimization ≠ autonomous mutation" in deliverables["DELIVERY_OPTIMIZATION_REPORT.md"]
    assert AUTONOMOUS_MUTATION_ENABLED_FIX_340 is False
