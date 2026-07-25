# SPDX-License-Identifier: Apache-2.0
"""PHASE_I2 — governed autonomous execution proof program tests."""

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
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_contract import (
    APPROVAL_BYPASS_FIX_362,
    AUTHORITY_EXPANSION_FIX_362,
    AUTONOMOUS_AUTHORITY_FIX_362,
    AUTONOMOUS_PROOF_REPEAT_MIN_SIZE,
    AUTONOMOUS_PROOF_RUN_MIN_SIZE,
    GOVERNANCE_BYPASS_FIX_362,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PHASES,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID,
    TRUST_PROMOTION_FIX_362,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_intent import (
    handle_autonomous_proof_intent,
    parse_autonomous_proof_intent,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_renderer import (
    render_all_autonomous_execution_proof_deliverables,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_service import (
    build_governed_autonomous_execution_proof_program,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_store import (
    clear_autonomous_proof_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_autonomous_proof_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_autonomous_proof_records_for_tests()


def _seed_execution_evidence(customer_session: str = "ws-i2-alpha") -> None:
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer delivery request: goal=Health endpoint, scope=small service, type=health_check_endpoint"
        ),
        session_id=customer_session,
    )
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True


def _seed_autonomous_execution_proof(program_session: str = "ws-i2") -> None:
    _seed_execution_evidence("ws-i2-alpha")
    handle_autonomous_proof_intent(
        parse_autonomous_proof_intent(
            "autonomous proof run: run_id=delivery-proof-1, category=delivery, outcome=passed, verification=verified"
        ),
        session_id=program_session,
    )
    handle_autonomous_proof_intent(
        parse_autonomous_proof_intent(
            "autonomous proof review approve: Human approves governed autonomous execution proof evidence"
        ),
        session_id=program_session,
    )


def test_phase_phases():
    assert GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID == "PHASE_I2"
    assert len(GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PHASES) == 9
    assert AUTONOMOUS_PROOF_RUN_MIN_SIZE == 1
    assert AUTONOMOUS_PROOF_REPEAT_MIN_SIZE == 2
    assert AUTONOMOUS_AUTHORITY_FIX_362 is False
    assert AUTHORITY_EXPANSION_FIX_362 is False
    assert GOVERNANCE_BYPASS_FIX_362 is False
    assert TRUST_PROMOTION_FIX_362 is False
    assert APPROVAL_BYPASS_FIX_362 is False


def test_intent_parsing():
    assert parse_autonomous_proof_intent("show autonomous execution proof dashboard") == {
        "action": "view",
        "focus": "autonomous_execution_proof_dashboard",
    }
    run = parse_autonomous_proof_intent(
        "autonomous proof run: run_id=run-1, category=delivery, verification=verified"
    )
    assert run["action"] == "run"


def test_program_phases_and_deliverables():
    _seed_autonomous_execution_proof(program_session="ws-i2-full")
    board = build_governed_autonomous_execution_proof_program(
        session_id="ws-i2-full"
    ).governed_autonomous_execution_proof_program
    assert board["phase_id"] == GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID
    assert board["autonomous_authority"] is False
    assert board["approval_bypass"] is False
    for phase in GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["autonomous_run_registry_demonstrated"] is True
    assert board["success_criteria"]["repeated_success_demonstrated"] is True
    assert board["success_criteria"]["repeated_recovery_demonstrated"] is True
    assert board["success_criteria"]["reduced_intervention_demonstrated"] is True
    assert board["success_criteria"]["verified_outcomes_demonstrated"] is True
    assert board["success_criteria"]["operational_consistency_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["success_evidence_score"] > 0
    assert board["metrics"]["autonomous_execution_proof_score"] >= 0.35

    deliverables = render_all_autonomous_execution_proof_deliverables(board)
    assert set(deliverables) == {
        "AUTONOMOUS_EXECUTION_PROOF_REPORT.md",
        "AUTONOMOUS_CAPABILITY_PROOF_MATRIX.md",
        "AUTONOMOUS_RECOVERY_ANALYSIS.md",
    }
    assert "Autonomous execution proof ≠ autonomous authority" in deliverables["AUTONOMOUS_EXECUTION_PROOF_REPORT.md"]
