# SPDX-License-Identifier: Apache-2.0
"""PHASE_I1 — autonomous execution maturity program tests."""

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
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_contract import (
    AUTHORITY_EXPANSION_FIX_361,
    AUTONOMOUS_AUTHORITY_FIX_361,
    AUTONOMOUS_EXECUTION_MATURITY_PHASES,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ID,
    AUTONOMOUS_EXECUTION_REQUEST_MIN_SIZE,
    GOVERNANCE_BYPASS_FIX_361,
    TRUST_PROMOTION_FIX_361,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_intent import (
    handle_autonomous_execution_intent,
    parse_autonomous_execution_intent,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_renderer import (
    render_all_autonomous_execution_deliverables,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_service import (
    build_autonomous_execution_maturity_program,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_store import (
    clear_autonomous_execution_records_for_tests,
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


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_autonomous_execution_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_autonomous_execution_records_for_tests()


def _seed_execution_evidence(customer_session: str = "ws-i1-alpha") -> None:
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer delivery request: goal=Health endpoint, scope=small service, type=health_check_endpoint"
        ),
        session_id=customer_session,
    )
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True


def _seed_autonomous_execution_maturity(program_session: str = "ws-i1") -> None:
    _seed_execution_evidence("ws-i1-alpha")
    handle_autonomous_execution_intent(
        parse_autonomous_execution_intent(
            "autonomous execution request: request_id=delivery-run-1, category=delivery, outcome=passed"
        ),
        session_id=program_session,
    )
    handle_autonomous_execution_intent(
        parse_autonomous_execution_intent(
            "autonomous execution review approve: Human approves governed autonomous execution maturity evidence"
        ),
        session_id=program_session,
    )


def test_phase_phases():
    assert AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ID == "PHASE_I1"
    assert len(AUTONOMOUS_EXECUTION_MATURITY_PHASES) == 9
    assert AUTONOMOUS_EXECUTION_REQUEST_MIN_SIZE == 1
    assert AUTONOMOUS_AUTHORITY_FIX_361 is False
    assert AUTHORITY_EXPANSION_FIX_361 is False
    assert GOVERNANCE_BYPASS_FIX_361 is False
    assert TRUST_PROMOTION_FIX_361 is False


def test_intent_parsing():
    assert parse_autonomous_execution_intent("show autonomous execution dashboard") == {
        "action": "view",
        "focus": "autonomous_execution_dashboard",
    }
    request = parse_autonomous_execution_intent(
        "autonomous execution request: request_id=run-1, category=delivery"
    )
    assert request["action"] == "request"


def test_program_phases_and_deliverables():
    _seed_autonomous_execution_maturity(program_session="ws-i1-full")
    board = build_autonomous_execution_maturity_program(
        session_id="ws-i1-full"
    ).autonomous_execution_maturity_program
    assert board["phase_id"] == AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ID
    assert board["autonomous_authority"] is False
    assert board["governance_bypass"] is False
    for phase in AUTONOMOUS_EXECUTION_MATURITY_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["initiative_monitoring_demonstrated"] is True
    assert board["success_criteria"]["planning_accuracy_demonstrated"] is True
    assert board["success_criteria"]["execution_success_demonstrated"] is True
    assert board["success_criteria"]["recovery_analysis_demonstrated"] is True
    assert board["success_criteria"]["human_intervention_analysis_demonstrated"] is True
    assert board["success_criteria"]["autonomous_learning_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["execution_success_rate"] > 0
    assert board["metrics"]["autonomous_execution_maturity_score"] >= 0.35

    deliverables = render_all_autonomous_execution_deliverables(board)
    assert set(deliverables) == {
        "AUTONOMOUS_EXECUTION_MATURITY_REPORT.md",
        "AUTONOMOUS_CAPABILITY_MATRIX.md",
        "HUMAN_INTERVENTION_ANALYSIS.md",
    }
    assert "Autonomous execution maturity ≠ autonomous authority" in deliverables["AUTONOMOUS_EXECUTION_MATURITY_REPORT.md"]
