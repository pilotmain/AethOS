# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F3 — multi-customer value proof tests."""

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
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_intent import (
    handle_customer_value_adoption_validation_intent,
    parse_customer_value_adoption_validation_intent,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    clear_customer_value_adoption_validation_records_for_tests,
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
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_contract import (
    AUTHORITY_EXPANSION_FIX_349,
    CUSTOMER_AUTHORITY_FIX_349,
    MULTI_CUSTOMER_VALUE_PROOF_PHASES,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ID,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_intent import (
    handle_multi_customer_value_proof_intent,
    parse_multi_customer_value_proof_intent,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_renderer import (
    render_all_multi_customer_value_proof_deliverables,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_service import (
    build_multi_customer_value_proof_program,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_store import (
    clear_multi_customer_value_proof_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_multi_customer_value_proof_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_multi_customer_value_proof_records_for_tests()


def _seed_customer_pilot(customer_session: str) -> None:
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer delivery request: goal=Health endpoint, scope=small service, type=health_check_endpoint"
        ),
        session_id=customer_session,
    )
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True
    handle_customer_value_adoption_validation_intent(
        parse_customer_value_adoption_validation_intent(
            "customer usage observation: workflow=health-check, endpoint=/health, executions=4, trend=continued"
        ),
        session_id=customer_session,
    )
    handle_customer_value_adoption_validation_intent(
        parse_customer_value_adoption_validation_intent(
            "customer usage observation: workflow=health-check, endpoint=/health, executions=6, trend=continued"
        ),
        session_id=customer_session,
    )


def _seed_multi_customer_proof(program_session: str = "ws-f3") -> None:
    for customer_id, customer_session in (("alpha", "ws-f3-alpha"), ("beta", "ws-f3-beta")):
        _seed_customer_pilot(customer_session)
        handle_multi_customer_value_proof_intent(
            parse_multi_customer_value_proof_intent(
                f"multi customer cohort: customer_id={customer_id}, "
                f"customer_session_id={customer_session}, use_case=health_check, "
                f"delivery_type=health_check_endpoint, environment=staging"
            ),
            session_id=program_session,
        )
    handle_multi_customer_value_proof_intent(
        parse_multi_customer_value_proof_intent(
            "multi customer review approve: Human approves multi-customer value proof evidence"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ID == "WORKSTREAM_F3"
    assert len(MULTI_CUSTOMER_VALUE_PROOF_PHASES) == 9
    assert CUSTOMER_AUTHORITY_FIX_349 is False
    assert AUTHORITY_EXPANSION_FIX_349 is False


def test_intent_parsing():
    assert parse_multi_customer_value_proof_intent("show multi customer value dashboard") == {
        "action": "view",
        "focus": "multi_customer_value_dashboard",
    }
    cohort = parse_multi_customer_value_proof_intent(
        "multi customer cohort: customer_id=alpha, use_case=health_check, environment=staging"
    )
    assert cohort["action"] == "cohort"


def test_program_phases_and_deliverables():
    _seed_multi_customer_proof(program_session="ws-f3-full")
    board = build_multi_customer_value_proof_program(session_id="ws-f3-full").multi_customer_value_proof_program
    assert board["workstream_id"] == MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ID
    assert board["customer_authority"] is False
    for phase in MULTI_CUSTOMER_VALUE_PROOF_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["multi_customer_cohort_registered"] is True
    assert board["success_criteria"]["repeatable_adoption"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["repeatability_score"] >= 1.0

    deliverables = render_all_multi_customer_value_proof_deliverables(board)
    assert set(deliverables) == {
        "MULTI_CUSTOMER_VALUE_PROOF_REPORT.md",
        "CUSTOMER_SUCCESS_PATTERNS_REPORT.md",
        "CUSTOMER_RETENTION_ANALYSIS_REPORT.md",
    }
    assert "Multi-customer validation ≠ customer authority" in deliverables["MULTI_CUSTOMER_VALUE_PROOF_REPORT.md"]
