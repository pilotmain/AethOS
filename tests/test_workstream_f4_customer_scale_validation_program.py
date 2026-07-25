# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F4 — customer scale validation tests."""

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
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_350,
    CUSTOMER_AUTHORITY_FIX_350,
    CUSTOMER_SCALE_VALIDATION_PHASES,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_ID,
    SCALE_COHORT_MIN_SIZE,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_intent import (
    handle_customer_scale_validation_intent,
    parse_customer_scale_validation_intent,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_renderer import (
    render_all_customer_scale_validation_deliverables,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_service import (
    build_customer_scale_validation_program,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_store import (
    clear_customer_scale_validation_records_for_tests,
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
    clear_customer_scale_validation_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_customer_scale_validation_records_for_tests()


def _seed_customer(customer_session: str, provider: str = "Railway") -> None:
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


def _seed_scale_validation(program_session: str = "ws-f4") -> None:
    customers = (
        ("alpha", "ws-f4-alpha", "Railway"),
        ("beta", "ws-f4-beta", "Vercel"),
        ("gamma", "ws-f4-gamma", "Railway"),
    )
    for customer_id, customer_session, provider in customers:
        _seed_customer(customer_session, provider=provider)
        handle_customer_scale_validation_intent(
            parse_customer_scale_validation_intent(
                f"customer scale cohort: customer_id={customer_id}, "
                f"customer_session_id={customer_session}, provider={provider}, environment=staging"
            ),
            session_id=program_session,
        )
    handle_customer_scale_validation_intent(
        parse_customer_scale_validation_intent(
            "customer scale review approve: Human approves customer scale validation evidence"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert CUSTOMER_SCALE_VALIDATION_PROGRAM_ID == "WORKSTREAM_F4"
    assert len(CUSTOMER_SCALE_VALIDATION_PHASES) == 9
    assert SCALE_COHORT_MIN_SIZE == 3
    assert CUSTOMER_AUTHORITY_FIX_350 is False
    assert AUTHORITY_EXPANSION_FIX_350 is False


def test_intent_parsing():
    assert parse_customer_scale_validation_intent("show customer scale dashboard") == {
        "action": "view",
        "focus": "customer_scale_dashboard",
    }
    cohort = parse_customer_scale_validation_intent(
        "customer scale cohort: customer_id=alpha, provider=Railway, environment=staging"
    )
    assert cohort["action"] == "cohort"


def test_program_phases_and_deliverables():
    _seed_scale_validation(program_session="ws-f4-full")
    board = build_customer_scale_validation_program(session_id="ws-f4-full").customer_scale_validation_program
    assert board["workstream_id"] == CUSTOMER_SCALE_VALIDATION_PROGRAM_ID
    assert board["customer_authority"] is False
    assert board["governance_bypass_authority"] is False
    for phase in CUSTOMER_SCALE_VALIDATION_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["scale_cohort_registered"] is True
    assert board["success_criteria"]["concurrent_delivery_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["concurrent_customers"] >= SCALE_COHORT_MIN_SIZE

    deliverables = render_all_customer_scale_validation_deliverables(board)
    assert set(deliverables) == {
        "CUSTOMER_SCALE_VALIDATION_REPORT.md",
        "EXECUTION_CAPACITY_REPORT.md",
        "CUSTOMER_OUTCOME_STABILITY_REPORT.md",
    }
    assert "Customer scale validation ≠ customer authority" in deliverables["CUSTOMER_SCALE_VALIDATION_REPORT.md"]
