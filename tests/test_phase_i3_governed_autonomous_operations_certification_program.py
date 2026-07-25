# SPDX-License-Identifier: Apache-2.0
"""PHASE_I3 — governed autonomous operations certification program tests."""

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
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_contract import (
    APPROVAL_BYPASS_FIX_363,
    AUTHORITY_EXPANSION_FIX_363,
    AUTONOMOUS_AUTHORITY_FIX_363,
    AUTONOMOUS_CERTIFICATION_CANDIDATE_MIN_SIZE,
    AUTONOMOUS_CERTIFICATION_SUSTAINED_MIN_SIZE,
    GOVERNANCE_BYPASS_FIX_363,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PHASES,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID,
    TRUST_PROMOTION_FIX_363,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_intent import (
    handle_autonomous_certification_intent,
    parse_autonomous_certification_intent,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_renderer import (
    render_all_autonomous_operations_certification_deliverables,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_service import (
    build_governed_autonomous_operations_certification_program,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_store import (
    clear_autonomous_certification_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_autonomous_certification_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_autonomous_certification_records_for_tests()


def _seed_execution_evidence(customer_session: str = "ws-i3-alpha") -> None:
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer delivery request: goal=Health endpoint, scope=small service, type=health_check_endpoint"
        ),
        session_id=customer_session,
    )
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True


def _seed_autonomous_operations_certification(program_session: str = "ws-i3") -> None:
    _seed_execution_evidence("ws-i3-alpha")
    handle_autonomous_certification_intent(
        parse_autonomous_certification_intent(
            "autonomous certification candidate: candidate_id=ops-cert-1, workload=delivery, provider=Railway"
        ),
        session_id=program_session,
    )
    handle_autonomous_certification_intent(
        parse_autonomous_certification_intent(
            "autonomous certification review approve: Human approves governed autonomous operations certification evidence"
        ),
        session_id=program_session,
    )


def test_phase_phases():
    assert GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID == "PHASE_I3"
    assert len(GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PHASES) == 9
    assert AUTONOMOUS_CERTIFICATION_CANDIDATE_MIN_SIZE == 1
    assert AUTONOMOUS_CERTIFICATION_SUSTAINED_MIN_SIZE == 2
    assert AUTONOMOUS_AUTHORITY_FIX_363 is False
    assert AUTHORITY_EXPANSION_FIX_363 is False
    assert GOVERNANCE_BYPASS_FIX_363 is False
    assert TRUST_PROMOTION_FIX_363 is False
    assert APPROVAL_BYPASS_FIX_363 is False


def test_intent_parsing():
    assert parse_autonomous_certification_intent("show autonomous operations certification dashboard") == {
        "action": "view",
        "focus": "autonomous_operations_certification_dashboard",
    }
    candidate = parse_autonomous_certification_intent(
        "autonomous certification candidate: candidate_id=cert-1, workload=delivery, provider=Railway"
    )
    assert candidate["action"] == "candidate"


def test_program_phases_and_deliverables():
    _seed_autonomous_operations_certification(program_session="ws-i3-full")
    board = build_governed_autonomous_operations_certification_program(
        session_id="ws-i3-full"
    ).governed_autonomous_operations_certification_program
    assert board["phase_id"] == GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID
    assert board["autonomous_authority"] is False
    assert board["approval_bypass"] is False
    for phase in GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["certification_candidate_registry_demonstrated"] is True
    assert board["success_criteria"]["sustained_execution_success_demonstrated"] is True
    assert board["success_criteria"]["sustained_deployment_success_demonstrated"] is True
    assert board["success_criteria"]["sustained_verification_success_demonstrated"] is True
    assert board["success_criteria"]["sustained_recovery_success_demonstrated"] is True
    assert board["success_criteria"]["declining_intervention_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["execution_reliability_score"] > 0
    assert board["metrics"]["autonomous_operations_certification_score"] >= 0.35

    deliverables = render_all_autonomous_operations_certification_deliverables(board)
    assert set(deliverables) == {
        "AUTONOMOUS_OPERATIONS_CERTIFICATION_REPORT.md",
        "AUTONOMOUS_CAPABILITY_CERTIFICATION_MATRIX.md",
        "AUTONOMOUS_RELIABILITY_CERTIFICATION_REPORT.md",
    }
    assert "Autonomous operations certification ≠ autonomous authority" in deliverables[
        "AUTONOMOUS_OPERATIONS_CERTIFICATION_REPORT.md"
    ]
