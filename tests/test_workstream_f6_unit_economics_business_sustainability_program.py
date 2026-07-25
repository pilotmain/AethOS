# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F6 — unit economics & business sustainability tests."""

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
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_contract import (
    AUTHORITY_EXPANSION_FIX_352,
    BILLING_EXECUTION_FIX_352,
    COMMERCIAL_AUTHORITY_FIX_352,
    ECONOMIC_COHORT_MIN_SIZE,
    FINANCIAL_FORECASTING_AS_FACT_FIX_352,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PHASES,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ID,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_intent import (
    handle_business_sustainability_intent,
    parse_business_sustainability_intent,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_renderer import (
    render_all_business_sustainability_deliverables,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_service import (
    build_unit_economics_business_sustainability_program,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_store import (
    clear_business_sustainability_records_for_tests,
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
    clear_business_sustainability_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_business_sustainability_records_for_tests()


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


def _seed_business_sustainability(program_session: str = "ws-f6") -> None:
    customers = (
        ("alpha", "ws-f6-alpha", "FREE", "startup"),
        ("beta", "ws-f6-beta", "PRO", "growth"),
        ("gamma", "ws-f6-gamma", "BUSINESS", "enterprise"),
    )
    for customer_id, customer_session, plan, segment in customers:
        _seed_customer(customer_session)
        handle_business_sustainability_intent(
            parse_business_sustainability_intent(
                f"business sustainability cohort: customer_id={customer_id}, "
                f"customer_session_id={customer_session}, plan={plan}, segment={segment}, "
                f"provider=Railway, support_profile=standard"
            ),
            session_id=program_session,
        )
    handle_business_sustainability_intent(
        parse_business_sustainability_intent(
            "business sustainability review approve: Human approves business sustainability evidence"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ID == "WORKSTREAM_F6"
    assert len(UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PHASES) == 9
    assert ECONOMIC_COHORT_MIN_SIZE == 3
    assert COMMERCIAL_AUTHORITY_FIX_352 is False
    assert BILLING_EXECUTION_FIX_352 is False
    assert FINANCIAL_FORECASTING_AS_FACT_FIX_352 is False
    assert AUTHORITY_EXPANSION_FIX_352 is False


def test_intent_parsing():
    assert parse_business_sustainability_intent("show business sustainability dashboard") == {
        "action": "view",
        "focus": "business_sustainability_dashboard",
    }
    cohort = parse_business_sustainability_intent(
        "business sustainability cohort: customer_id=alpha, plan=PRO, segment=startup"
    )
    assert cohort["action"] == "cohort"


def test_program_phases_and_deliverables():
    _seed_business_sustainability(program_session="ws-f6-full")
    board = build_unit_economics_business_sustainability_program(
        session_id="ws-f6-full"
    ).unit_economics_business_sustainability_program
    assert board["workstream_id"] == UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ID
    assert board["commercial_authority"] is False
    assert board["billing_execution"] is False
    assert board["financial_forecasting_as_fact"] is False
    for phase in UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["economic_cohort_registered"] is True
    assert board["success_criteria"]["sustainable_delivery_economics"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["delivery_cost"] > 0
    assert board["metrics"]["sustainability_score"] >= 0.5

    deliverables = render_all_business_sustainability_deliverables(board)
    assert set(deliverables) == {
        "BUSINESS_SUSTAINABILITY_REPORT.md",
        "UNIT_ECONOMICS_REPORT.md",
        "RETENTION_ECONOMICS_REPORT.md",
    }
    assert "Economic validation ≠ commercial authority" in deliverables["BUSINESS_SUSTAINABILITY_REPORT.md"]
