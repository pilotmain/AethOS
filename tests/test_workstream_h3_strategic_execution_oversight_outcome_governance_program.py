# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H3 — strategic execution oversight tests."""

from __future__ import annotations

import pytest

from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_intent import (
    handle_strategic_execution_intent,
    parse_strategic_execution_intent,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_store import (
    clear_strategic_execution_records_for_tests,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_contract import (
    AUTHORITY_EXPANSION_FIX_360,
    EXECUTION_AUTHORITY_FIX_360,
    OVERSIGHT_INITIATIVE_MIN_SIZE,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PHASES,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ID,
    STRATEGY_MUTATION_FIX_360,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_intent import (
    handle_strategic_oversight_intent,
    parse_strategic_oversight_intent,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_renderer import (
    render_all_strategic_oversight_deliverables,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_service import (
    build_strategic_execution_oversight_outcome_governance_program,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_store import (
    clear_strategic_oversight_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_strategic_execution_records_for_tests()
    clear_strategic_oversight_records_for_tests()
    yield
    clear_strategic_execution_records_for_tests()
    clear_strategic_oversight_records_for_tests()


def _seed_h2_initiative(program_session: str = "ws-h3") -> None:
    handle_strategic_execution_intent(
        parse_strategic_execution_intent(
            "strategic execution initiative: initiative_id=growth-alpha, "
            "growth_path=customer_acquisition_expansion, "
            "objective=Expand pilot customer acquisition through governed delivery"
        ),
        session_id=program_session,
    )
    handle_strategic_execution_intent(
        parse_strategic_execution_intent(
            "strategic execution review approve: Human approves governed strategic execution plan"
        ),
        session_id=program_session,
    )


def _seed_strategic_oversight(program_session: str = "ws-h3") -> None:
    _seed_h2_initiative(program_session)
    for milestone in (
        "planning_complete",
        "governance_ready",
        "execution_started",
        "outcome_measured",
    ):
        handle_strategic_oversight_intent(
            parse_strategic_oversight_intent(
                f"strategic oversight milestone: initiative_id=growth-alpha, "
                f"milestone={milestone}, status=complete"
            ),
            session_id=program_session,
        )
    handle_strategic_oversight_intent(
        parse_strategic_oversight_intent(
            "strategic oversight status: initiative_id=growth-alpha, status=monitoring"
        ),
        session_id=program_session,
    )
    handle_strategic_oversight_intent(
        parse_strategic_oversight_intent(
            "strategic oversight review approve: Human approves strategic outcome governance"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ID == "WORKSTREAM_H3"
    assert len(STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PHASES) == 9
    assert OVERSIGHT_INITIATIVE_MIN_SIZE == 1
    assert EXECUTION_AUTHORITY_FIX_360 is False
    assert STRATEGY_MUTATION_FIX_360 is False
    assert AUTHORITY_EXPANSION_FIX_360 is False


def test_intent_parsing():
    assert parse_strategic_oversight_intent("show strategic oversight dashboard") == {
        "action": "view",
        "focus": "strategic_oversight_dashboard",
    }
    milestone = parse_strategic_oversight_intent(
        "strategic oversight milestone: initiative_id=alpha, milestone=planning_complete, status=complete"
    )
    assert milestone["action"] == "milestone"


def test_program_phases_and_deliverables():
    _seed_strategic_oversight(program_session="ws-h3-full")
    board = build_strategic_execution_oversight_outcome_governance_program(
        session_id="ws-h3-full"
    ).strategic_execution_oversight_outcome_governance_program
    assert board["workstream_id"] == STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ID
    assert board["execution_authority"] is False
    assert board["strategy_mutation"] is False
    for phase in STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["initiative_monitoring_demonstrated"] is True
    assert board["success_criteria"]["outcome_tracking_demonstrated"] is True
    assert board["success_criteria"]["milestone_governance_demonstrated"] is True
    assert board["success_criteria"]["risk_monitoring_demonstrated"] is True
    assert board["success_criteria"]["strategic_learning_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["initiative_success_rate"] == 1.0
    assert board["metrics"]["oversight_maturity_level"] in {"learning", "adaptive", "measured"}

    deliverables = render_all_strategic_oversight_deliverables(board)
    assert set(deliverables) == {
        "STRATEGIC_OVERSIGHT_REPORT.md",
        "INITIATIVE_OUTCOME_REPORT.md",
        "STRATEGIC_LEARNING_REPORT.md",
    }
    assert "Strategic oversight ≠ execution authority" in deliverables["STRATEGIC_OVERSIGHT_REPORT.md"]
