# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G3 — revenue density & business viability tests."""

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
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_contract import (
    AUTHORITY_EXPANSION_FIX_356,
    BILLING_EXECUTION_FIX_356,
    COMMERCIAL_AUTHORITY_FIX_356,
    PAYMENT_PROCESSING_FIX_356,
    REVENUE_COHORT_MIN_SIZE,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PHASES,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ID,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_intent import (
    handle_revenue_density_intent,
    parse_revenue_density_intent,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_renderer import (
    render_all_revenue_density_deliverables,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_service import (
    build_revenue_density_business_viability_program,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_store import (
    clear_revenue_density_records_for_tests,
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
    clear_revenue_density_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_revenue_density_records_for_tests()


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


def _seed_revenue_density(program_session: str = "ws-g3") -> None:
    customers = (
        ("alpha", "ws-g3-alpha", "FREE", "startup"),
        ("beta", "ws-g3-beta", "PRO", "growth"),
        ("gamma", "ws-g3-gamma", "BUSINESS", "enterprise"),
    )
    for customer_id, customer_session, plan, segment in customers:
        _seed_customer(customer_session)
        handle_revenue_density_intent(
            parse_revenue_density_intent(
                f"revenue density cohort: customer_id={customer_id}, "
                f"customer_session_id={customer_session}, plan={plan}, segment={segment}"
            ),
            session_id=program_session,
        )
    handle_revenue_density_intent(
        parse_revenue_density_intent(
            "revenue density review approve: Human approves revenue density validation evidence"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ID == "WORKSTREAM_G3"
    assert len(REVENUE_DENSITY_BUSINESS_VIABILITY_PHASES) == 9
    assert REVENUE_COHORT_MIN_SIZE == 3
    assert COMMERCIAL_AUTHORITY_FIX_356 is False
    assert PAYMENT_PROCESSING_FIX_356 is False
    assert BILLING_EXECUTION_FIX_356 is False
    assert AUTHORITY_EXPANSION_FIX_356 is False


def test_intent_parsing():
    assert parse_revenue_density_intent("show business viability dashboard") == {
        "action": "view",
        "focus": "business_viability_dashboard",
    }
    cohort = parse_revenue_density_intent(
        "revenue density cohort: customer_id=alpha, plan=PRO, segment=startup"
    )
    assert cohort["action"] == "cohort"


def test_program_phases_and_deliverables():
    _seed_revenue_density(program_session="ws-g3-full")
    board = build_revenue_density_business_viability_program(
        session_id="ws-g3-full"
    ).revenue_density_business_viability_program
    assert board["workstream_id"] == REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ID
    assert board["commercial_authority"] is False
    assert board["payment_processing"] is False
    assert board["billing_execution"] is False
    for phase in REVENUE_DENSITY_BUSINESS_VIABILITY_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["revenue_cohort_registered"] is True
    assert board["success_criteria"]["plan_engagement_demonstrated"] is True
    assert board["success_criteria"]["expansion_potential_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["revenue_density_score"] > 0
    assert board["metrics"]["business_viability_score"] >= 0.5

    deliverables = render_all_revenue_density_deliverables(board)
    assert set(deliverables) == {
        "REVENUE_DENSITY_REPORT.md",
        "BUSINESS_VIABILITY_REPORT.md",
        "EXPANSION_SIGNAL_REPORT.md",
    }
    assert "Revenue density ≠ commercial authority" in deliverables["REVENUE_DENSITY_REPORT.md"]
