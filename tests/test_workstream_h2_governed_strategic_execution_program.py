# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H2 — governed strategic execution program tests."""

from __future__ import annotations

import pytest

from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_contract import (
    AUTHORITY_EXPANSION_FIX_359,
    EXECUTION_AUTHORITY_FIX_359,
    GOVERNED_STRATEGIC_EXECUTION_PHASES,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ID,
    STRATEGIC_EXECUTION_AUTHORITY_FIX_359,
    STRATEGIC_INITIATIVE_MIN_SIZE,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_intent import (
    handle_strategic_execution_intent,
    parse_strategic_execution_intent,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_renderer import (
    render_all_strategic_execution_deliverables,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_service import (
    build_governed_strategic_execution_program,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_store import (
    clear_strategic_execution_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_strategic_execution_records_for_tests()
    yield
    clear_strategic_execution_records_for_tests()


def _seed_strategic_execution(program_session: str = "ws-h2") -> None:
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


def test_workstream_phases():
    assert GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ID == "WORKSTREAM_H2"
    assert len(GOVERNED_STRATEGIC_EXECUTION_PHASES) == 9
    assert STRATEGIC_INITIATIVE_MIN_SIZE == 1
    assert STRATEGIC_EXECUTION_AUTHORITY_FIX_359 is False
    assert EXECUTION_AUTHORITY_FIX_359 is False
    assert AUTHORITY_EXPANSION_FIX_359 is False


def test_intent_parsing():
    assert parse_strategic_execution_intent("show strategic execution dashboard") == {
        "action": "view",
        "focus": "strategic_execution_dashboard",
    }
    initiative = parse_strategic_execution_intent(
        "strategic execution initiative: initiative_id=alpha, growth_path=enterprise_expansion"
    )
    assert initiative["action"] == "initiative"


def test_program_phases_and_deliverables():
    _seed_strategic_execution(program_session="ws-h2-full")
    board = build_governed_strategic_execution_program(
        session_id="ws-h2-full"
    ).governed_strategic_execution_program
    assert board["workstream_id"] == GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ID
    assert board["strategic_execution_authority"] is False
    assert board["execution_authority"] is False
    assert board["budget_allocation"] is False
    for phase in GOVERNED_STRATEGIC_EXECUTION_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["strategic_initiative_planning_demonstrated"] is True
    assert board["success_criteria"]["dependency_identification_demonstrated"] is True
    assert board["success_criteria"]["governance_planning_demonstrated"] is True
    assert board["success_criteria"]["execution_readiness_assessed"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["execution_readiness_level"] == "approved"
    assert board["metrics"]["execution_readiness_score"] >= 0.35

    deliverables = render_all_strategic_execution_deliverables(board)
    assert set(deliverables) == {
        "STRATEGIC_EXECUTION_REPORT.md",
        "INITIATIVE_DEPENDENCY_ANALYSIS.md",
        "EXECUTION_READINESS_REPORT.md",
    }
    assert "Strategic execution planning ≠ strategic execution authority" in deliverables["STRATEGIC_EXECUTION_REPORT.md"]
