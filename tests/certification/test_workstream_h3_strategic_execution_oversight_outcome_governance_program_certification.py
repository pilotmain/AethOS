# SPDX-License-Identifier: Apache-2.0
"""FIX 360 / WORKSTREAM_H3 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_360_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_contract import (
    AUTHORITY_EXPANSION_FIX_360,
    AUTOMATIC_INITIATIVE_CHANGES_FIX_360,
    BUDGET_ALLOCATION_FIX_360,
    EXECUTION_AUTHORITY_FIX_360,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_360,
    GOVERNANCE_BYPASS_FIX_360,
    LOCAL_STRATEGIC_OVERSIGHT_EXECUTABLE_FIX_360,
    RESOURCE_COMMITMENT_FIX_360,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PHASES,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_FIX,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ID,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_INVARIANT,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ROUTE_ID,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_SCHEMA_VERSION,
    STRATEGY_MUTATION_FIX_360,
    TRUST_MUTATION_AUTHORITY_FIX_360,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_service import (
    build_strategic_execution_oversight_outcome_governance_program,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_store import (
    clear_strategic_oversight_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-h3-cert-360"


@pytest.fixture(autouse=True)
def _clean():
    clear_strategic_oversight_records_for_tests()
    yield
    clear_strategic_oversight_records_for_tests()


class TestWorkstreamH3StrategicExecutionOversightCertification:
    def test_fix_360_contract(self) -> None:
        assert STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_FIX == "FIX 360"
        assert STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ID == "WORKSTREAM_H3"
        assert STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_SCHEMA_VERSION == (
            "workstream_strategic_execution_oversight_outcome_governance_program_v1"
        )
        assert EXECUTION_AUTHORITY_FIX_360 is False
        assert STRATEGY_MUTATION_FIX_360 is False
        assert BUDGET_ALLOCATION_FIX_360 is False
        assert RESOURCE_COMMITMENT_FIX_360 is False
        assert GOVERNANCE_BYPASS_FIX_360 is False
        assert AUTOMATIC_INITIATIVE_CHANGES_FIX_360 is False
        assert AUTHORITY_EXPANSION_FIX_360 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_360 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_360 is False
        assert LOCAL_STRATEGIC_OVERSIGHT_EXECUTABLE_FIX_360 is True

    def test_fix_360_oversight_not_execution_authority(self) -> None:
        board = build_strategic_execution_oversight_outcome_governance_program(
            session_id=SESSION
        ).strategic_execution_oversight_outcome_governance_program
        assert set(board["fix_360_certification_requirements"]) == set(FIX_360_CERTIFICATION_REQUIREMENTS)
        assert board["execution_authority"] is False
        assert "execution_authority" in STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_INVARIANT

    def test_fix_360_phases_present(self) -> None:
        sections = build_strategic_execution_oversight_outcome_governance_program(
            session_id=SESSION
        ).strategic_execution_oversight_outcome_governance_program["sections"]
        for phase in STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PHASES:
            assert sections[phase]

    def test_fix_360_certification_requirement_count(self) -> None:
        assert len(FIX_360_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_360_route_id(self) -> None:
        assert STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ROUTE_ID == (
            "workstream_strategic_execution_oversight_outcome_governance_program"
        )
