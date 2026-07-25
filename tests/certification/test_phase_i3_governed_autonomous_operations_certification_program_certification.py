# SPDX-License-Identifier: Apache-2.0
"""FIX 363 / PHASE_I3 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_363_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_contract import (
    APPROVAL_BYPASS_FIX_363,
    AUTHORITY_EXPANSION_FIX_363,
    AUTONOMOUS_AUTHORITY_FIX_363,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_363,
    GOVERNANCE_BYPASS_FIX_363,
    GOVERNANCE_MUTATION_FIX_363,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PHASES,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_FIX,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_INVARIANT,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ROUTE_ID,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_SCHEMA_VERSION,
    LOCAL_GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_EXECUTABLE_FIX_363,
    TRUST_MUTATION_AUTHORITY_FIX_363,
    TRUST_PROMOTION_FIX_363,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_service import (
    build_governed_autonomous_operations_certification_program,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_store import (
    clear_autonomous_certification_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-i3-cert-363"


@pytest.fixture(autouse=True)
def _clean():
    clear_autonomous_certification_records_for_tests()
    yield
    clear_autonomous_certification_records_for_tests()


class TestPhaseI3GovernedAutonomousOperationsCertificationCertification:
    def test_fix_363_contract(self) -> None:
        assert GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_FIX == "FIX 363"
        assert GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ID == "PHASE_I3"
        assert GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_SCHEMA_VERSION == (
            "phase_governed_autonomous_operations_certification_program_v1"
        )
        assert AUTONOMOUS_AUTHORITY_FIX_363 is False
        assert AUTHORITY_EXPANSION_FIX_363 is False
        assert GOVERNANCE_MUTATION_FIX_363 is False
        assert GOVERNANCE_BYPASS_FIX_363 is False
        assert TRUST_PROMOTION_FIX_363 is False
        assert APPROVAL_BYPASS_FIX_363 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_363 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_363 is False
        assert LOCAL_GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_EXECUTABLE_FIX_363 is True

    def test_fix_363_certification_not_autonomous_authority(self) -> None:
        board = build_governed_autonomous_operations_certification_program(
            session_id=SESSION
        ).governed_autonomous_operations_certification_program
        assert set(board["fix_363_certification_requirements"]) == set(FIX_363_CERTIFICATION_REQUIREMENTS)
        assert board["autonomous_authority"] is False
        assert "autonomous_authority" in GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_INVARIANT

    def test_fix_363_phases_present(self) -> None:
        sections = build_governed_autonomous_operations_certification_program(
            session_id=SESSION
        ).governed_autonomous_operations_certification_program["sections"]
        for phase in GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PHASES:
            assert sections[phase]

    def test_fix_363_certification_requirement_count(self) -> None:
        assert len(FIX_363_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_363_route_id(self) -> None:
        assert GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ROUTE_ID == (
            "phase_governed_autonomous_operations_certification_program"
        )
