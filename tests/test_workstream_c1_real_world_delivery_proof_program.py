# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C1 — real world delivery proof program tests."""

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
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_contract import (
    AUTHORITY_EXPANSION_FIX_339,
    REAL_WORLD_DELIVERY_PROOF_PHASES,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_ID,
    WAVE_1_REPOSITORIES,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_executor import (
    run_delivery_proof,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_intent import (
    handle_real_world_delivery_proof_intent,
    parse_real_world_delivery_proof_intent,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_renderer import (
    render_all_real_world_delivery_proof_deliverables,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_service import (
    build_real_world_delivery_proof_program,
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
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_real_world_delivery_proof_records_for_tests()


def _seed_and_run(session_id: str = "ws-c1") -> None:
    handle_real_world_delivery_proof_intent(
        parse_real_world_delivery_proof_intent(
            "delivery proof candidate: repository=aethos type=documentation_update"
        ),
        session_id=session_id,
    )
    handle_real_world_delivery_proof_intent(
        parse_real_world_delivery_proof_intent("delivery proof note: Wave 1 AethOS documentation proof run"),
        session_id=session_id,
    )
    result = run_delivery_proof(
        session_id=session_id,
        repository="aethos",
        candidate_type="documentation_update",
    )
    assert result["passed"] is True
    handle_real_world_delivery_proof_intent(
        parse_real_world_delivery_proof_intent(
            "delivery proof review approve: Human approves real-world delivery proof evidence"
        ),
        session_id=session_id,
    )


def test_workstream_phases():
    assert REAL_WORLD_DELIVERY_PROOF_PROGRAM_ID == "WORKSTREAM_C1"
    assert len(REAL_WORLD_DELIVERY_PROOF_PHASES) == 9
    assert len(WAVE_1_REPOSITORIES) == 4


def test_intent_parsing():
    assert parse_real_world_delivery_proof_intent("show delivery proof dashboard") == {
        "action": "view",
        "focus": "delivery_proof_dashboard",
    }
    parsed = parse_real_world_delivery_proof_intent(
        "delivery proof review approve: Human approves governed real-world proof only"
    )
    assert parsed == {
        "action": "record",
        "kind": "delivery_proof_review_approve",
        "content": "Human approves governed real-world proof only",
    }
    run_intent = parse_real_world_delivery_proof_intent(
        "delivery proof run: repository=pilotos type=bug_fix"
    )
    assert run_intent["action"] == "run"
    assert run_intent["repository"] == "pilotos"


def test_program_phases_and_outputs():
    result = build_real_world_delivery_proof_program(session_id="ws-c1-empty")
    board = result.real_world_delivery_proof_program
    assert board["workstream_id"] == REAL_WORLD_DELIVERY_PROOF_PROGRAM_ID
    assert board["authority_expansion"] is False
    assert board["trust_mutation_authority"] is False
    for phase in REAL_WORLD_DELIVERY_PROOF_PHASES:
        assert phase in board["sections"]


def test_delivery_proof_execution_and_program_completion():
    _seed_and_run(session_id="ws-c1-run")
    board = build_real_world_delivery_proof_program(session_id="ws-c1-run").real_world_delivery_proof_program
    assert board["success_criteria"]["successful_deliveries"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["successful_deliveries"] >= 1


def test_documentation_proof_skips_deployment():
    result = run_delivery_proof(
        session_id="ws-c1-docs",
        repository="nexora",
        candidate_type="documentation_update",
    )
    assert result["passed"] is True
    deployment = result["execution"]["stage_results"]["execution_track_4"]
    assert deployment.get("skipped") is True


def test_deliverable_renderers():
    _seed_and_run(session_id="ws-c1-render")
    board = build_real_world_delivery_proof_program(session_id="ws-c1-render").real_world_delivery_proof_program
    deliverables = render_all_real_world_delivery_proof_deliverables(board)
    assert set(deliverables) == {
        "REAL_WORLD_DELIVERY_PROOF_REPORT.md",
        "DELIVERY_RELIABILITY_REPORT.md",
        "DELIVERY_TRUST_IMPACT_REPORT.md",
    }
    assert "Operational proof ≠ authority expansion" in deliverables["REAL_WORLD_DELIVERY_PROOF_REPORT.md"]
    assert AUTHORITY_EXPANSION_FIX_339 is False
