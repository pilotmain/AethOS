# SPDX-License-Identifier: Apache-2.0
"""FIX 359 / WORKSTREAM_H2 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_359_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_contract import (
    AUTHORITY_EXPANSION_FIX_359,
    AUTOMATIC_PRIORITIZATION_FIX_359,
    BUDGET_ALLOCATION_FIX_359,
    EXECUTION_AUTHORITY_FIX_359,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_359,
    GOVERNED_STRATEGIC_EXECUTION_PHASES,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_FIX,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ID,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_INVARIANT,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ROUTE_ID,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_SCHEMA_VERSION,
    INITIATIVE_LAUNCH_FIX_359,
    LOCAL_STRATEGIC_EXECUTION_EXECUTABLE_FIX_359,
    PROJECT_CREATION_FIX_359,
    RESOURCE_COMMITMENT_FIX_359,
    ROADMAP_MUTATION_FIX_359,
    STRATEGIC_EXECUTION_AUTHORITY_FIX_359,
    TRUST_MUTATION_AUTHORITY_FIX_359,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_service import (
    build_governed_strategic_execution_program,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_store import (
    clear_strategic_execution_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-h2-cert-359"


@pytest.fixture(autouse=True)
def _clean():
    clear_strategic_execution_records_for_tests()
    yield
    clear_strategic_execution_records_for_tests()


class TestWorkstreamH2GovernedStrategicExecutionCertification:
    def test_fix_359_contract(self) -> None:
        assert GOVERNED_STRATEGIC_EXECUTION_PROGRAM_FIX == "FIX 359"
        assert GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ID == "WORKSTREAM_H2"
        assert GOVERNED_STRATEGIC_EXECUTION_PROGRAM_SCHEMA_VERSION == (
            "workstream_governed_strategic_execution_program_v1"
        )
        assert STRATEGIC_EXECUTION_AUTHORITY_FIX_359 is False
        assert EXECUTION_AUTHORITY_FIX_359 is False
        assert BUDGET_ALLOCATION_FIX_359 is False
        assert PROJECT_CREATION_FIX_359 is False
        assert RESOURCE_COMMITMENT_FIX_359 is False
        assert INITIATIVE_LAUNCH_FIX_359 is False
        assert ROADMAP_MUTATION_FIX_359 is False
        assert AUTHORITY_EXPANSION_FIX_359 is False
        assert AUTOMATIC_PRIORITIZATION_FIX_359 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_359 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_359 is False
        assert LOCAL_STRATEGIC_EXECUTION_EXECUTABLE_FIX_359 is True

    def test_fix_359_planning_not_execution_authority(self) -> None:
        board = build_governed_strategic_execution_program(
            session_id=SESSION
        ).governed_strategic_execution_program
        assert set(board["fix_359_certification_requirements"]) == set(FIX_359_CERTIFICATION_REQUIREMENTS)
        assert board["strategic_execution_authority"] is False
        assert "execution_authority" in GOVERNED_STRATEGIC_EXECUTION_PROGRAM_INVARIANT

    def test_fix_359_phases_present(self) -> None:
        sections = build_governed_strategic_execution_program(
            session_id=SESSION
        ).governed_strategic_execution_program["sections"]
        for phase in GOVERNED_STRATEGIC_EXECUTION_PHASES:
            assert sections[phase]

    def test_fix_359_certification_requirement_count(self) -> None:
        assert len(FIX_359_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_359_route_id(self) -> None:
        assert GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ROUTE_ID == (
            "workstream_governed_strategic_execution_program"
        )
