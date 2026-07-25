# SPDX-License-Identifier: Apache-2.0
"""FIX 361 / PHASE_I1 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_361_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_contract import (
    AUTHORITY_EXPANSION_FIX_361,
    AUTONOMOUS_AUTHORITY_FIX_361,
    AUTONOMOUS_EXECUTION_MATURITY_PHASES,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_FIX,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ID,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_INVARIANT,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ROUTE_ID,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_SCHEMA_VERSION,
    AUTONOMOUS_ORGANIZATIONAL_CONTROL_FIX_361,
    AUTONOMOUS_STRATEGIC_CONTROL_FIX_361,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_361,
    GOVERNANCE_BYPASS_FIX_361,
    GOVERNANCE_MUTATION_FIX_361,
    LOCAL_AUTONOMOUS_EXECUTION_MATURITY_EXECUTABLE_FIX_361,
    TRUST_MUTATION_AUTHORITY_FIX_361,
    TRUST_PROMOTION_FIX_361,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_service import (
    build_autonomous_execution_maturity_program,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_store import (
    clear_autonomous_execution_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-i1-cert-361"


@pytest.fixture(autouse=True)
def _clean():
    clear_autonomous_execution_records_for_tests()
    yield
    clear_autonomous_execution_records_for_tests()


class TestPhaseI1AutonomousExecutionMaturityCertification:
    def test_fix_361_contract(self) -> None:
        assert AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_FIX == "FIX 361"
        assert AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ID == "PHASE_I1"
        assert AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_SCHEMA_VERSION == (
            "phase_autonomous_execution_maturity_program_v1"
        )
        assert AUTONOMOUS_AUTHORITY_FIX_361 is False
        assert AUTHORITY_EXPANSION_FIX_361 is False
        assert GOVERNANCE_MUTATION_FIX_361 is False
        assert GOVERNANCE_BYPASS_FIX_361 is False
        assert TRUST_PROMOTION_FIX_361 is False
        assert AUTONOMOUS_ORGANIZATIONAL_CONTROL_FIX_361 is False
        assert AUTONOMOUS_STRATEGIC_CONTROL_FIX_361 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_361 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_361 is False
        assert LOCAL_AUTONOMOUS_EXECUTION_MATURITY_EXECUTABLE_FIX_361 is True

    def test_fix_361_maturity_not_autonomous_authority(self) -> None:
        board = build_autonomous_execution_maturity_program(
            session_id=SESSION
        ).autonomous_execution_maturity_program
        assert set(board["fix_361_certification_requirements"]) == set(FIX_361_CERTIFICATION_REQUIREMENTS)
        assert board["autonomous_authority"] is False
        assert "autonomous_authority" in AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_INVARIANT

    def test_fix_361_phases_present(self) -> None:
        sections = build_autonomous_execution_maturity_program(
            session_id=SESSION
        ).autonomous_execution_maturity_program["sections"]
        for phase in AUTONOMOUS_EXECUTION_MATURITY_PHASES:
            assert sections[phase]

    def test_fix_361_certification_requirement_count(self) -> None:
        assert len(FIX_361_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_361_route_id(self) -> None:
        assert AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ROUTE_ID == (
            "phase_autonomous_execution_maturity_program"
        )
