# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G2 — real usage density & platform adoption tests."""

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
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_contract import (
    AUTHORITY_EXPANSION_FIX_355,
    AUTOMATED_OUTREACH_FIX_355,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PHASES,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ID,
    USER_AUTHORITY_FIX_355,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_intent import (
    handle_platform_adoption_intent,
    parse_platform_adoption_intent,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_renderer import (
    render_all_platform_adoption_deliverables,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_service import (
    build_real_usage_density_platform_adoption_program,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_store import (
    clear_platform_adoption_records_for_tests,
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
    clear_platform_adoption_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_platform_adoption_records_for_tests()


def _seed_usage(customer_session: str = "ws-g2-alpha") -> None:
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


def _seed_platform_adoption(program_session: str = "ws-g2") -> None:
    _seed_usage("ws-g2-alpha")
    handle_platform_adoption_intent(
        parse_platform_adoption_intent(
            "platform adoption session: customer_session_id=ws-g2-alpha, surface=mission_control"
        ),
        session_id=program_session,
    )
    handle_platform_adoption_intent(
        parse_platform_adoption_intent(
            "platform adoption review approve: Human approves platform adoption validation evidence"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ID == "WORKSTREAM_G2"
    assert len(REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PHASES) == 9
    assert USER_AUTHORITY_FIX_355 is False
    assert AUTOMATED_OUTREACH_FIX_355 is False
    assert AUTHORITY_EXPANSION_FIX_355 is False


def test_intent_parsing():
    assert parse_platform_adoption_intent("show platform adoption dashboard") == {
        "action": "view",
        "focus": "platform_adoption_dashboard",
    }
    session = parse_platform_adoption_intent(
        "platform adoption session: customer_session_id=alpha, surface=mission_control"
    )
    assert session["action"] == "session"


def test_program_phases_and_deliverables():
    _seed_platform_adoption(program_session="ws-g2-full")
    board = build_real_usage_density_platform_adoption_program(
        session_id="ws-g2-full"
    ).real_usage_density_platform_adoption_program
    assert board["workstream_id"] == REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ID
    assert board["user_authority"] is False
    assert board["automated_outreach"] is False
    for phase in REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["active_usage_demonstrated"] is True
    assert board["success_criteria"]["retained_usage_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["active_users"] > 0
    assert board["metrics"]["platform_dependence_score"] >= 0.5

    deliverables = render_all_platform_adoption_deliverables(board)
    assert set(deliverables) == {
        "REAL_USAGE_DENSITY_REPORT.md",
        "PLATFORM_ADOPTION_REPORT.md",
        "PLATFORM_DEPENDENCE_ANALYSIS.md",
    }
    assert "Usage density ≠ user authority" in deliverables["REAL_USAGE_DENSITY_REPORT.md"]
