# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G4 — enterprise platform maturity & readiness audit tests."""

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
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_contract import (
    AUTHORITY_EXPANSION_FIX_357,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PHASES,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ID,
    LAUNCH_AUTHORITY_FIX_357,
    TRUST_PROMOTION_FIX_357,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_intent import (
    handle_platform_maturity_intent,
    parse_platform_maturity_intent,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_renderer import (
    render_all_platform_maturity_deliverables,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_service import (
    build_enterprise_platform_maturity_readiness_audit_program,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_store import (
    clear_platform_maturity_records_for_tests,
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
    clear_platform_maturity_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_platform_maturity_records_for_tests()


def _seed_operational_evidence(customer_session: str = "ws-g4-alpha") -> None:
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


def _seed_platform_maturity(program_session: str = "ws-g4") -> None:
    _seed_operational_evidence("ws-g4-alpha")
    handle_platform_maturity_intent(
        parse_platform_maturity_intent(
            "platform maturity review approve: Human approves enterprise platform maturity audit evidence"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ID == "WORKSTREAM_G4"
    assert len(ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PHASES) == 9
    assert LAUNCH_AUTHORITY_FIX_357 is False
    assert TRUST_PROMOTION_FIX_357 is False
    assert AUTHORITY_EXPANSION_FIX_357 is False


def test_intent_parsing():
    assert parse_platform_maturity_intent("show enterprise platform maturity dashboard") == {
        "action": "view",
        "focus": "enterprise_platform_maturity_dashboard",
    }
    note = parse_platform_maturity_intent("platform maturity note: Architecture coverage verified")
    assert note["action"] == "record"


def test_program_phases_and_deliverables():
    _seed_platform_maturity(program_session="ws-g4-full")
    board = build_enterprise_platform_maturity_readiness_audit_program(
        session_id="ws-g4-full"
    ).enterprise_platform_maturity_readiness_audit_program
    assert board["workstream_id"] == ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ID
    assert board["launch_authority"] is False
    assert board["trust_promotion"] is False
    for phase in ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["platform_inventory_complete"] is True
    assert board["success_criteria"]["architecture_maturity_assessed"] is True
    assert board["success_criteria"]["execution_maturity_assessed"] is True
    assert board["success_criteria"]["evidence_maturity_assessed"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["overall_platform_maturity_score"] > 0

    deliverables = render_all_platform_maturity_deliverables(board)
    assert set(deliverables) == {
        "ENTERPRISE_PLATFORM_MATURITY_REPORT.md",
        "PLATFORM_READINESS_AUDIT.md",
        "PLATFORM_GAP_ANALYSIS.md",
    }
    assert "Platform maturity audit ≠ launch authority" in deliverables["ENTERPRISE_PLATFORM_MATURITY_REPORT.md"]
