# SPDX-License-Identifier: Apache-2.0
"""FIX 362 / PHASE_I2 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_362_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_contract import (
    APPROVAL_BYPASS_FIX_362,
    AUTHORITY_EXPANSION_FIX_362,
    AUTONOMOUS_AUTHORITY_FIX_362,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_362,
    GOVERNANCE_BYPASS_FIX_362,
    GOVERNANCE_MUTATION_FIX_362,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PHASES,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_FIX,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_INVARIANT,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ROUTE_ID,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_SCHEMA_VERSION,
    LOCAL_GOVERNED_AUTONOMOUS_EXECUTION_PROOF_EXECUTABLE_FIX_362,
    TRUST_MUTATION_AUTHORITY_FIX_362,
    TRUST_PROMOTION_FIX_362,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_service import (
    build_governed_autonomous_execution_proof_program,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_store import (
    clear_autonomous_proof_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-i2-cert-362"


@pytest.fixture(autouse=True)
def _clean():
    clear_autonomous_proof_records_for_tests()
    yield
    clear_autonomous_proof_records_for_tests()


class TestPhaseI2GovernedAutonomousExecutionProofCertification:
    def test_fix_362_contract(self) -> None:
        assert GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_FIX == "FIX 362"
        assert GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ID == "PHASE_I2"
        assert GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_SCHEMA_VERSION == (
            "phase_governed_autonomous_execution_proof_program_v1"
        )
        assert AUTONOMOUS_AUTHORITY_FIX_362 is False
        assert AUTHORITY_EXPANSION_FIX_362 is False
        assert GOVERNANCE_MUTATION_FIX_362 is False
        assert GOVERNANCE_BYPASS_FIX_362 is False
        assert TRUST_PROMOTION_FIX_362 is False
        assert APPROVAL_BYPASS_FIX_362 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_362 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_362 is False
        assert LOCAL_GOVERNED_AUTONOMOUS_EXECUTION_PROOF_EXECUTABLE_FIX_362 is True

    def test_fix_362_proof_not_autonomous_authority(self) -> None:
        board = build_governed_autonomous_execution_proof_program(
            session_id=SESSION
        ).governed_autonomous_execution_proof_program
        assert set(board["fix_362_certification_requirements"]) == set(FIX_362_CERTIFICATION_REQUIREMENTS)
        assert board["autonomous_authority"] is False
        assert "autonomous_authority" in GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_INVARIANT

    def test_fix_362_phases_present(self) -> None:
        sections = build_governed_autonomous_execution_proof_program(
            session_id=SESSION
        ).governed_autonomous_execution_proof_program["sections"]
        for phase in GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PHASES:
            assert sections[phase]

    def test_fix_362_certification_requirement_count(self) -> None:
        assert len(FIX_362_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_362_route_id(self) -> None:
        assert GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ROUTE_ID == (
            "phase_governed_autonomous_execution_proof_program"
        )
