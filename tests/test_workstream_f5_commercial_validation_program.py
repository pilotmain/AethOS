# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F5 — commercial validation tests."""

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
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_351,
    COMMERCIAL_AUTHORITY_FIX_351,
    COMMERCIAL_COHORT_MIN_SIZE,
    COMMERCIAL_VALIDATION_PHASES,
    COMMERCIAL_VALIDATION_PROGRAM_ID,
    PAYMENT_PROCESSING_FIX_351,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_intent import (
    handle_commercial_validation_intent,
    parse_commercial_validation_intent,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_renderer import (
    render_all_commercial_validation_deliverables,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_service import (
    build_commercial_validation_program,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_store import (
    clear_commercial_validation_records_for_tests,
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


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_commercial_validation_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_commercial_validation_records_for_tests()


def _seed_customer(customer_session: str) -> None:
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


def _seed_commercial_validation(program_session: str = "ws-f5") -> None:
    customers = (
        ("alpha", "ws-f5-alpha", "FREE", "startup"),
        ("beta", "ws-f5-beta", "PRO", "growth"),
        ("gamma", "ws-f5-gamma", "BUSINESS", "enterprise"),
    )
    for customer_id, customer_session, plan, segment in customers:
        _seed_customer(customer_session)
        handle_commercial_validation_intent(
            parse_commercial_validation_intent(
                f"commercial validation cohort: customer_id={customer_id}, "
                f"customer_session_id={customer_session}, plan={plan}, segment={segment}, environment=staging"
            ),
            session_id=program_session,
        )
    handle_commercial_validation_intent(
        parse_commercial_validation_intent(
            "commercial validation review approve: Human approves commercial validation evidence"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert COMMERCIAL_VALIDATION_PROGRAM_ID == "WORKSTREAM_F5"
    assert len(COMMERCIAL_VALIDATION_PHASES) == 9
    assert COMMERCIAL_COHORT_MIN_SIZE == 3
    assert COMMERCIAL_AUTHORITY_FIX_351 is False
    assert PAYMENT_PROCESSING_FIX_351 is False
    assert AUTHORITY_EXPANSION_FIX_351 is False


def test_intent_parsing():
    assert parse_commercial_validation_intent("show commercial validation dashboard") == {
        "action": "view",
        "focus": "commercial_validation_dashboard",
    }
    cohort = parse_commercial_validation_intent(
        "commercial validation cohort: customer_id=alpha, plan=PRO, segment=startup"
    )
    assert cohort["action"] == "cohort"


def test_program_phases_and_deliverables():
    _seed_commercial_validation(program_session="ws-f5-full")
    board = build_commercial_validation_program(session_id="ws-f5-full").commercial_validation_program
    assert board["workstream_id"] == COMMERCIAL_VALIDATION_PROGRAM_ID
    assert board["commercial_authority"] is False
    assert board["payment_processing"] is False
    assert board["governance_bypass_authority"] is False
    for phase in COMMERCIAL_VALIDATION_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["commercial_cohort_registered"] is True
    assert board["success_criteria"]["plan_attractiveness_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["activation_rate"] >= 0.5

    deliverables = render_all_commercial_validation_deliverables(board)
    assert set(deliverables) == {
        "COMMERCIAL_VALIDATION_REPORT.md",
        "COMMERCIAL_RETENTION_REPORT.md",
        "VALUE_TO_REVENUE_ANALYSIS.md",
    }
    assert "Commercial validation ≠ commercial authority" in deliverables["COMMERCIAL_VALIDATION_REPORT.md"]
