# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D2 — multi-cloud operational proof program tests."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store import (
    clear_governed_deployment_execution_records_for_tests,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    clear_governed_git_delivery_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_contract import (
    ALL_PROOF_PROVIDERS,
    AUTHORITY_EXPANSION_FIX_342,
    MULTI_CLOUD_OPERATIONAL_PROOF_PHASES,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ID,
    PROVIDER_AUTHORITY_FIX_342,
    WAVE_1_PROVIDERS,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_executor import (
    run_provider_proof,
    run_wave1_provider_proof,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_intent import (
    handle_multi_cloud_operational_proof_intent,
    parse_multi_cloud_operational_proof_intent,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_renderer import (
    render_all_multi_cloud_operational_proof_deliverables,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_service import (
    build_multi_cloud_operational_proof_program,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_store import (
    clear_multi_cloud_operational_proof_records_for_tests,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_store import (
    clear_phase2_provider_execution_expansion_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_phase2_provider_execution_expansion_records_for_tests()
    clear_multi_cloud_operational_proof_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_phase2_provider_execution_expansion_records_for_tests()
    clear_multi_cloud_operational_proof_records_for_tests()


def test_workstream_phases():
    assert MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ID == "WORKSTREAM_D2"
    assert len(MULTI_CLOUD_OPERATIONAL_PROOF_PHASES) == 9
    assert len(WAVE_1_PROVIDERS) == 4
    assert len(ALL_PROOF_PROVIDERS) == 6


def test_intent_parsing():
    assert parse_multi_cloud_operational_proof_intent("show multi cloud dashboard") == {
        "action": "view",
        "focus": "multi_cloud_dashboard",
    }
    run = parse_multi_cloud_operational_proof_intent("provider proof run: provider=aws environment=staging")
    assert run["action"] == "run"
    assert run["provider"] == "aws"
    review = parse_multi_cloud_operational_proof_intent(
        "provider proof review approve: Human approves Wave 1 multi-cloud operational proof"
    )
    assert review["kind"] == "provider_proof_review_approve"


def test_program_phases_and_outputs():
    board = build_multi_cloud_operational_proof_program(session_id="ws-d2-empty").multi_cloud_operational_proof_program
    assert board["workstream_id"] == MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ID
    assert board["provider_authority"] is False
    assert board["authority_expansion"] is False
    for phase in MULTI_CLOUD_OPERATIONAL_PROOF_PHASES:
        assert phase in board["sections"]


def test_wave1_provider_proof():
    session_id = "ws-d2-wave1"
    wave = run_wave1_provider_proof(session_id=session_id)
    assert wave["passed_count"] == len(WAVE_1_PROVIDERS)
    assert wave["ok"] is True

    handle_multi_cloud_operational_proof_intent(
        parse_multi_cloud_operational_proof_intent(
            "provider proof review approve: Human approves Wave 1 multi-cloud operational proof"
        ),
        session_id=session_id,
    )

    board = build_multi_cloud_operational_proof_program(session_id=session_id).multi_cloud_operational_proof_program
    assert board["success_criteria"]["wave_1_multi_cloud_proven"] is True
    assert board["success_criteria"]["program_complete"] is True
    scorecard = board["sections"]["phase_7_comparative_analysis"][0]["provider_maturity_scorecard"]
    assert scorecard["wave_1_multi_cloud_proven"] is True


def test_railway_provider_proof():
    result = run_provider_proof(session_id="ws-d2-railway", provider="railway")
    assert result["passed"] is True
    assert result["provider"] == "Railway"
    assert result["provider_authority_granted"] is False


def test_deliverable_renderers():
    run_provider_proof(session_id="ws-d2-render", provider="gcp")
    board = build_multi_cloud_operational_proof_program(session_id="ws-d2-render").multi_cloud_operational_proof_program
    deliverables = render_all_multi_cloud_operational_proof_deliverables(board)
    assert set(deliverables) == {
        "MULTI_CLOUD_OPERATIONAL_PROOF_REPORT.md",
        "PROVIDER_RELIABILITY_REPORT.md",
        "PROVIDER_MATURITY_SCORECARD.md",
    }
    assert "Multi-cloud proof ≠ provider authority" in deliverables["MULTI_CLOUD_OPERATIONAL_PROOF_REPORT.md"]
    assert PROVIDER_AUTHORITY_FIX_342 is False
    assert AUTHORITY_EXPANSION_FIX_342 is False
