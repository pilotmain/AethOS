# SPDX-License-Identifier: Apache-2.0
"""PHASE_J1 — production reality & longitudinal operations program tests."""

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
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_contract import (
    APPROVAL_BYPASS_FIX_364,
    AUTHORITY_EXPANSION_FIX_364,
    AUTONOMOUS_PRODUCTION_CONTROL_FIX_364,
    DURABILITY_LEVELS,
    OPERATIONAL_AUTHORITY_FIX_364,
    PRODUCTION_OPERATIONS_MIN_SIZE,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PHASES,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ID,
    PRODUCTION_SUSTAINED_MIN_SIZE,
    TRUST_PROMOTION_FIX_364,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_intent import (
    handle_production_reality_intent,
    parse_production_reality_intent,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_renderer import (
    render_all_production_reality_deliverables,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_service import (
    build_production_reality_longitudinal_operations_program,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_store import (
    clear_production_reality_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_production_reality_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_production_reality_records_for_tests()


def _seed_execution_evidence(customer_session: str = "ws-j1-alpha") -> None:
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer delivery request: goal=Health endpoint, scope=small service, type=health_check_endpoint"
        ),
        session_id=customer_session,
    )
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True


def _seed_production_reality(program_session: str = "ws-j1") -> None:
    _seed_execution_evidence("ws-j1-alpha")
    handle_production_reality_intent(
        parse_production_reality_intent(
            "production reality observation: operation_id=prod-ops-1, category=deployment, outcome=passed, provider=Railway"
        ),
        session_id=program_session,
    )
    handle_production_reality_intent(
        parse_production_reality_intent(
            "production reality review approve: Human approves production reality longitudinal operations evidence"
        ),
        session_id=program_session,
    )


def test_phase_phases():
    assert PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ID == "PHASE_J1"
    assert len(PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PHASES) == 9
    assert len(DURABILITY_LEVELS) == 5
    assert PRODUCTION_OPERATIONS_MIN_SIZE == 1
    assert PRODUCTION_SUSTAINED_MIN_SIZE == 2
    assert OPERATIONAL_AUTHORITY_FIX_364 is False
    assert AUTONOMOUS_PRODUCTION_CONTROL_FIX_364 is False
    assert AUTHORITY_EXPANSION_FIX_364 is False
    assert TRUST_PROMOTION_FIX_364 is False
    assert APPROVAL_BYPASS_FIX_364 is False


def test_intent_parsing():
    assert parse_production_reality_intent("show production reality dashboard") == {
        "action": "view",
        "focus": "production_reality_dashboard",
    }
    observation = parse_production_reality_intent(
        "production reality observation: operation_id=ops-1, category=deployment, provider=Railway"
    )
    assert observation["action"] == "observation"


def test_program_phases_and_deliverables():
    _seed_production_reality(program_session="ws-j1-full")
    board = build_production_reality_longitudinal_operations_program(
        session_id="ws-j1-full"
    ).production_reality_longitudinal_operations_program
    assert board["phase_id"] == PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ID
    assert board["operational_authority"] is False
    assert board["autonomous_production_control"] is False
    assert board["approval_bypass"] is False
    for phase in PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["production_operations_registry_demonstrated"] is True
    assert board["success_criteria"]["sustained_operation_demonstrated"] is True
    assert board["success_criteria"]["deployment_durability_demonstrated"] is True
    assert board["success_criteria"]["recovery_durability_demonstrated"] is True
    assert board["success_criteria"]["provider_durability_demonstrated"] is True
    assert board["success_criteria"]["customer_durability_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["deployment_durability_score"] > 0
    assert board["metrics"]["operational_durability_score"] >= 0.35

    deliverables = render_all_production_reality_deliverables(board)
    assert set(deliverables) == {
        "PRODUCTION_REALITY_REPORT.md",
        "LONGITUDINAL_OPERATIONS_REPORT.md",
        "PRODUCTION_DURABILITY_ANALYSIS.md",
    }
    assert "Production reality measurement ≠ operational authority" in deliverables["PRODUCTION_REALITY_REPORT.md"]
