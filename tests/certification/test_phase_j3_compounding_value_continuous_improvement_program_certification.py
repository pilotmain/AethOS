# SPDX-License-Identifier: Apache-2.0
"""FIX 366 / PHASE_J3 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_366_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_contract import (
    AUTHORITY_EXPANSION_FIX_366,
    AUTOMATIC_POLICY_CHANGES_FIX_366,
    AUTONOMOUS_SELF_MODIFICATION_FIX_366,
    AUTONOMOUS_STRATEGIC_CONTROL_FIX_366,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PHASES,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_FIX,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ID,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_INVARIANT,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ROUTE_ID,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_SCHEMA_VERSION,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_366,
    GOVERNANCE_BYPASS_FIX_366,
    GOVERNANCE_MUTATION_FIX_366,
    LOCAL_COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_EXECUTABLE_FIX_366,
    TRUST_MUTATION_AUTHORITY_FIX_366,
    TRUST_PROMOTION_FIX_366,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_service import (
    build_compounding_value_continuous_improvement_program,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_store import (
    clear_continuous_improvement_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-j3-cert-366"


@pytest.fixture(autouse=True)
def _clean():
    clear_continuous_improvement_records_for_tests()
    yield
    clear_continuous_improvement_records_for_tests()


class TestPhaseJ3CompoundingValueContinuousImprovementCertification:
    def test_fix_366_contract(self) -> None:
        assert COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_FIX == "FIX 366"
        assert COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ID == "PHASE_J3"
        assert COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_SCHEMA_VERSION == (
            "phase_compounding_value_continuous_improvement_program_v1"
        )
        assert AUTONOMOUS_SELF_MODIFICATION_FIX_366 is False
        assert AUTOMATIC_POLICY_CHANGES_FIX_366 is False
        assert AUTONOMOUS_STRATEGIC_CONTROL_FIX_366 is False
        assert AUTHORITY_EXPANSION_FIX_366 is False
        assert GOVERNANCE_MUTATION_FIX_366 is False
        assert GOVERNANCE_BYPASS_FIX_366 is False
        assert TRUST_PROMOTION_FIX_366 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_366 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_366 is False
        assert LOCAL_COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_EXECUTABLE_FIX_366 is True

    def test_fix_366_improvement_not_self_modification(self) -> None:
        board = build_compounding_value_continuous_improvement_program(
            session_id=SESSION
        ).compounding_value_continuous_improvement_program
        assert set(board["fix_366_certification_requirements"]) == set(FIX_366_CERTIFICATION_REQUIREMENTS)
        assert board["autonomous_self_modification"] is False
        assert "autonomous_self_modification" in COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_INVARIANT

    def test_fix_366_phases_present(self) -> None:
        sections = build_compounding_value_continuous_improvement_program(
            session_id=SESSION
        ).compounding_value_continuous_improvement_program["sections"]
        for phase in COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PHASES:
            assert sections[phase]

    def test_fix_366_certification_requirement_count(self) -> None:
        assert len(FIX_366_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_366_route_id(self) -> None:
        assert COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ROUTE_ID == (
            "phase_compounding_value_continuous_improvement_program"
        )
