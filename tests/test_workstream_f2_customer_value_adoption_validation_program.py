# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F2 — customer value & adoption validation tests."""

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
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_348,
    CUSTOMER_MANIPULATION_FIX_348,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PHASES,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ID,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_intent import (
    handle_customer_value_adoption_validation_intent,
    parse_customer_value_adoption_validation_intent,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_renderer import (
    render_all_customer_value_adoption_validation_deliverables,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_service import (
    build_customer_value_adoption_validation_program,
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
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()


def _seed_f1_delivery(session_id: str) -> None:
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer delivery request: goal=Health endpoint, scope=small service, type=health_check_endpoint"
        ),
        session_id=session_id,
    )
    assert run_customer_delivery_pilot(session_id=session_id)["passed"] is True


def _seed_f2_validation(session_id: str) -> None:
    _seed_f1_delivery(session_id)
    handle_customer_value_adoption_validation_intent(
        parse_customer_value_adoption_validation_intent(
            "customer usage observation: workflow=health-check, endpoint=/health, executions=3, trend=continued"
        ),
        session_id=session_id,
    )
    handle_customer_value_adoption_validation_intent(
        parse_customer_value_adoption_validation_intent(
            "customer usage observation: workflow=health-check, endpoint=/health, executions=5, trend=continued"
        ),
        session_id=session_id,
    )
    handle_customer_value_adoption_validation_intent(
        parse_customer_value_adoption_validation_intent(
            "customer value note: Customer repeated health-check workflow without onboarding friction"
        ),
        session_id=session_id,
    )
    handle_customer_value_adoption_validation_intent(
        parse_customer_value_adoption_validation_intent(
            "customer value review approve: Human approves customer value and adoption validation evidence"
        ),
        session_id=session_id,
    )


def test_workstream_phases():
    assert CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ID == "WORKSTREAM_F2"
    assert len(CUSTOMER_VALUE_ADOPTION_VALIDATION_PHASES) == 9
    assert CUSTOMER_MANIPULATION_FIX_348 is False
    assert AUTHORITY_EXPANSION_FIX_348 is False


def test_intent_parsing():
    assert parse_customer_value_adoption_validation_intent("show customer value dashboard") == {
        "action": "view",
        "focus": "customer_value_dashboard",
    }
    usage = parse_customer_value_adoption_validation_intent(
        "customer usage observation: workflow=health-check, executions=2"
    )
    assert usage["action"] == "observe"


def test_program_phases_and_deliverables():
    _seed_f2_validation(session_id="ws-f2-full")
    board = build_customer_value_adoption_validation_program(
        session_id="ws-f2-full"
    ).customer_value_adoption_validation_program
    assert board["workstream_id"] == CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ID
    assert board["customer_manipulation"] is False
    assert board["automated_outreach"] is False
    for phase in CUSTOMER_VALUE_ADOPTION_VALIDATION_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["program_complete"] is True
    assert board["success_criteria"]["repeat_usage_evidence"] is True

    deliverables = render_all_customer_value_adoption_validation_deliverables(board)
    assert set(deliverables) == {
        "CUSTOMER_ADOPTION_VALIDATION_REPORT.md",
        "CUSTOMER_VALUE_VALIDATION_REPORT.md",
        "CUSTOMER_RETENTION_REPORT.md",
    }
    assert "Value validation ≠ customer manipulation" in deliverables["CUSTOMER_ADOPTION_VALIDATION_REPORT.md"]
