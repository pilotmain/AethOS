# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H1 — strategic direction & next-growth decision tests."""

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
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_contract import (
    AUTHORITY_EXPANSION_FIX_358,
    STRATEGIC_AUTHORITY_FIX_358,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PHASES,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ID,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_intent import (
    handle_strategic_direction_intent,
    parse_strategic_direction_intent,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_renderer import (
    render_all_strategic_direction_deliverables,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_service import (
    build_strategic_direction_next_growth_decision_program,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_store import (
    clear_strategic_direction_records_for_tests,
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
    clear_strategic_direction_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_strategic_direction_records_for_tests()


def _seed_operational_evidence(customer_session: str = "ws-h1-alpha") -> None:
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


def _seed_strategic_direction(program_session: str = "ws-h1") -> None:
    _seed_operational_evidence("ws-h1-alpha")
    handle_strategic_direction_intent(
        parse_strategic_direction_intent(
            "strategic direction review approve: Human approves strategic direction intelligence evidence"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ID == "WORKSTREAM_H1"
    assert len(STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PHASES) == 9
    assert STRATEGIC_AUTHORITY_FIX_358 is False
    assert AUTHORITY_EXPANSION_FIX_358 is False


def test_intent_parsing():
    assert parse_strategic_direction_intent("show strategic direction dashboard") == {
        "action": "view",
        "focus": "strategic_direction_dashboard",
    }
    note = parse_strategic_direction_intent("strategic direction note: Customer growth path favored")
    assert note["action"] == "record"


def test_program_phases_and_deliverables():
    _seed_strategic_direction(program_session="ws-h1-full")
    board = build_strategic_direction_next_growth_decision_program(
        session_id="ws-h1-full"
    ).strategic_direction_next_growth_decision_program
    assert board["workstream_id"] == STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ID
    assert board["strategic_authority"] is False
    assert board["budget_allocation"] is False
    for phase in STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["strategic_baseline_composed"] is True
    assert board["success_criteria"]["growth_opportunities_evaluated"] is True
    assert board["success_criteria"]["strategic_tradeoffs_analyzed"] is True
    assert board["success_criteria"]["evidence_backed_confidence"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["growth_potential_score"] >= 0

    deliverables = render_all_strategic_direction_deliverables(board)
    assert set(deliverables) == {
        "STRATEGIC_DIRECTION_REPORT.md",
        "NEXT_GROWTH_OPTIONS_REPORT.md",
        "STRATEGIC_TRADEOFF_ANALYSIS.md",
    }
    assert "Strategic direction intelligence ≠ strategic authority" in deliverables["STRATEGIC_DIRECTION_REPORT.md"]
