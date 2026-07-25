# SPDX-License-Identifier: Apache-2.0
"""PHASE_J3 — compounding value & continuous improvement program tests."""

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
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_contract import (
    AUTHORITY_EXPANSION_FIX_366,
    AUTOMATIC_POLICY_CHANGES_FIX_366,
    AUTONOMOUS_SELF_MODIFICATION_FIX_366,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PHASES,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ID,
    IMPROVEMENT_BASELINE_MIN_SIZE,
    IMPROVEMENT_LEVELS,
    TRUST_PROMOTION_FIX_366,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_intent import (
    handle_continuous_improvement_intent,
    parse_continuous_improvement_intent,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_renderer import (
    render_all_compounding_value_deliverables,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_service import (
    build_compounding_value_continuous_improvement_program,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_store import (
    clear_continuous_improvement_records_for_tests,
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
    clear_continuous_improvement_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_continuous_improvement_records_for_tests()


def _seed_execution_evidence(customer_session: str = "ws-j3-alpha") -> None:
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer delivery request: goal=Health endpoint, scope=small service, type=health_check_endpoint"
        ),
        session_id=customer_session,
    )
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True


def _seed_compounding_value(program_session: str = "ws-j3") -> None:
    _seed_execution_evidence("ws-j3-alpha")
    handle_continuous_improvement_intent(
        parse_continuous_improvement_intent(
            "continuous improvement baseline: baseline_id=delivery-baseline, category=delivery, initial_score=0.35, current_score=0.6"
        ),
        session_id=program_session,
    )
    handle_continuous_improvement_intent(
        parse_continuous_improvement_intent(
            "continuous improvement review approve: Human approves compounding value continuous improvement evidence"
        ),
        session_id=program_session,
    )


def test_phase_phases():
    assert COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ID == "PHASE_J3"
    assert len(COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PHASES) == 9
    assert len(IMPROVEMENT_LEVELS) == 5
    assert IMPROVEMENT_BASELINE_MIN_SIZE == 1
    assert AUTONOMOUS_SELF_MODIFICATION_FIX_366 is False
    assert AUTOMATIC_POLICY_CHANGES_FIX_366 is False
    assert AUTHORITY_EXPANSION_FIX_366 is False
    assert TRUST_PROMOTION_FIX_366 is False


def test_intent_parsing():
    assert parse_continuous_improvement_intent("show compounding value dashboard") == {
        "action": "view",
        "focus": "compounding_value_dashboard",
    }
    baseline = parse_continuous_improvement_intent(
        "continuous improvement baseline: baseline_id=base-1, category=delivery, initial_score=0.3"
    )
    assert baseline["action"] == "baseline"


def test_program_phases_and_deliverables():
    _seed_compounding_value(program_session="ws-j3-full")
    board = build_compounding_value_continuous_improvement_program(
        session_id="ws-j3-full"
    ).compounding_value_continuous_improvement_program
    assert board["phase_id"] == COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ID
    assert board["autonomous_self_modification"] is False
    assert board["automatic_policy_changes"] is False
    for phase in COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["improvement_baseline_registry_demonstrated"] is True
    assert board["success_criteria"]["improving_delivery_outcomes_demonstrated"] is True
    assert board["success_criteria"]["improving_deployment_outcomes_demonstrated"] is True
    assert board["success_criteria"]["improving_customer_outcomes_demonstrated"] is True
    assert board["success_criteria"]["improving_recovery_outcomes_demonstrated"] is True
    assert board["success_criteria"]["improving_business_outcomes_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["compounding_value_score"] >= 0.2

    deliverables = render_all_compounding_value_deliverables(board)
    assert set(deliverables) == {
        "COMPOUNDING_VALUE_REPORT.md",
        "CONTINUOUS_IMPROVEMENT_REPORT.md",
        "LEARNING_EFFECTIVENESS_REPORT.md",
    }
    assert "Continuous improvement measurement ≠ autonomous self-modification" in deliverables["COMPOUNDING_VALUE_REPORT.md"]
