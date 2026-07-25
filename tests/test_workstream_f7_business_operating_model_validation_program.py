# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F7 — business operating model validation tests."""

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
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_353,
    BUSINESS_OPERATING_MODEL_VALIDATION_PHASES,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ID,
    GOVERNANCE_MUTATION_FIX_353,
    OPERATING_AUTHORITY_FIX_353,
    OPERATING_MODEL_COHORT_MIN_SIZE,
    PROVIDER_MUTATION_FIX_353,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_intent import (
    handle_operating_model_intent,
    parse_operating_model_intent,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_renderer import (
    render_all_business_operating_model_deliverables,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_service import (
    build_business_operating_model_validation_program,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_store import (
    clear_operating_model_records_for_tests,
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
    clear_operating_model_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_operating_model_records_for_tests()


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


def _seed_operating_model(program_session: str = "ws-f7") -> None:
    customers = (
        ("alpha", "ws-f7-alpha", "Railway", "FREE"),
        ("beta", "ws-f7-beta", "Vercel", "PRO"),
        ("gamma", "ws-f7-gamma", "Railway", "BUSINESS"),
    )
    for customer_id, customer_session, provider, plan in customers:
        _seed_customer(customer_session)
        handle_operating_model_intent(
            parse_operating_model_intent(
                f"operating model cohort: customer_id={customer_id}, "
                f"customer_session_id={customer_session}, provider={provider}, plan={plan}, "
                f"support_profile=standard, segment=startup"
            ),
            session_id=program_session,
        )
    handle_operating_model_intent(
        parse_operating_model_intent(
            "operating model review approve: Human approves operating model validation evidence"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ID == "WORKSTREAM_F7"
    assert len(BUSINESS_OPERATING_MODEL_VALIDATION_PHASES) == 9
    assert OPERATING_MODEL_COHORT_MIN_SIZE == 3
    assert OPERATING_AUTHORITY_FIX_353 is False
    assert GOVERNANCE_MUTATION_FIX_353 is False
    assert PROVIDER_MUTATION_FIX_353 is False
    assert AUTHORITY_EXPANSION_FIX_353 is False


def test_intent_parsing():
    assert parse_operating_model_intent("show operating model dashboard") == {
        "action": "view",
        "focus": "operating_model_dashboard",
    }
    cohort = parse_operating_model_intent(
        "operating model cohort: customer_id=alpha, provider=Railway, plan=PRO"
    )
    assert cohort["action"] == "cohort"


def test_program_phases_and_deliverables():
    _seed_operating_model(program_session="ws-f7-full")
    board = build_business_operating_model_validation_program(
        session_id="ws-f7-full"
    ).business_operating_model_validation_program
    assert board["workstream_id"] == BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ID
    assert board["operating_authority"] is False
    assert board["governance_mutation"] is False
    assert board["provider_mutation"] is False
    for phase in BUSINESS_OPERATING_MODEL_VALIDATION_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["operating_model_cohort_registered"] is True
    assert board["success_criteria"]["sustainable_delivery_capacity"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["delivery_efficiency"] > 0
    assert board["metrics"]["business_sustainability_score"] >= 0.5

    deliverables = render_all_business_operating_model_deliverables(board)
    assert set(deliverables) == {
        "BUSINESS_OPERATING_MODEL_REPORT.md",
        "DELIVERY_SUSTAINABILITY_REPORT.md",
        "OPERATING_MODEL_SUSTAINABILITY_REPORT.md",
    }
    assert "Operating model validation ≠ operating authority" in deliverables["BUSINESS_OPERATING_MODEL_REPORT.md"]
