# SPDX-License-Identifier: Apache-2.0
"""FIX 358 / WORKSTREAM_H1 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_358_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_contract import (
    AUTHORITY_EXPANSION_FIX_358,
    AUTOMATIC_PRIORITIZATION_FIX_358,
    BUDGET_ALLOCATION_FIX_358,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_358,
    LOCAL_STRATEGIC_DIRECTION_EXECUTABLE_FIX_358,
    PLAN_EXECUTION_FIX_358,
    PROJECT_CREATION_FIX_358,
    RESOURCE_COMMITMENT_FIX_358,
    ROADMAP_MUTATION_FIX_358,
    STRATEGIC_AUTHORITY_FIX_358,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PHASES,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_FIX,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ID,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_INVARIANT,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ROUTE_ID,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_358,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_service import (
    build_strategic_direction_next_growth_decision_program,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_store import (
    clear_strategic_direction_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-h1-cert-358"


@pytest.fixture(autouse=True)
def _clean():
    clear_strategic_direction_records_for_tests()
    yield
    clear_strategic_direction_records_for_tests()


class TestWorkstreamH1StrategicDirectionNextGrowthCertification:
    def test_fix_358_contract(self) -> None:
        assert STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_FIX == "FIX 358"
        assert STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ID == "WORKSTREAM_H1"
        assert STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_SCHEMA_VERSION == (
            "workstream_strategic_direction_next_growth_decision_program_v1"
        )
        assert STRATEGIC_AUTHORITY_FIX_358 is False
        assert BUDGET_ALLOCATION_FIX_358 is False
        assert PROJECT_CREATION_FIX_358 is False
        assert RESOURCE_COMMITMENT_FIX_358 is False
        assert PLAN_EXECUTION_FIX_358 is False
        assert ROADMAP_MUTATION_FIX_358 is False
        assert AUTHORITY_EXPANSION_FIX_358 is False
        assert AUTOMATIC_PRIORITIZATION_FIX_358 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_358 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_358 is False
        assert LOCAL_STRATEGIC_DIRECTION_EXECUTABLE_FIX_358 is True

    def test_fix_358_direction_not_strategic_authority(self) -> None:
        board = build_strategic_direction_next_growth_decision_program(
            session_id=SESSION
        ).strategic_direction_next_growth_decision_program
        assert set(board["fix_358_certification_requirements"]) == set(FIX_358_CERTIFICATION_REQUIREMENTS)
        assert board["strategic_authority"] is False
        assert "strategic_authority" in STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_INVARIANT

    def test_fix_358_phases_present(self) -> None:
        sections = build_strategic_direction_next_growth_decision_program(
            session_id=SESSION
        ).strategic_direction_next_growth_decision_program["sections"]
        for phase in STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PHASES:
            assert sections[phase]

    def test_fix_358_certification_requirement_count(self) -> None:
        assert len(FIX_358_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_358_route_id(self) -> None:
        assert STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ROUTE_ID == (
            "workstream_strategic_direction_next_growth_decision_program"
        )
