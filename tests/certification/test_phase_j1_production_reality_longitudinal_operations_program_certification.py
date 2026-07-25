# SPDX-License-Identifier: Apache-2.0
"""FIX 364 / PHASE_J1 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_364_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_contract import (
    APPROVAL_BYPASS_FIX_364,
    AUTHORITY_EXPANSION_FIX_364,
    AUTONOMOUS_PRODUCTION_CONTROL_FIX_364,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_364,
    GOVERNANCE_BYPASS_FIX_364,
    GOVERNANCE_MUTATION_FIX_364,
    LOCAL_PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_EXECUTABLE_FIX_364,
    OPERATIONAL_AUTHORITY_FIX_364,
    OPERATIONAL_AUTOMATION_CHANGES_FIX_364,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PHASES,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_FIX,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ID,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_INVARIANT,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ROUTE_ID,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_364,
    TRUST_PROMOTION_FIX_364,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_service import (
    build_production_reality_longitudinal_operations_program,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_store import (
    clear_production_reality_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-j1-cert-364"


@pytest.fixture(autouse=True)
def _clean():
    clear_production_reality_records_for_tests()
    yield
    clear_production_reality_records_for_tests()


class TestPhaseJ1ProductionRealityLongitudinalOperationsCertification:
    def test_fix_364_contract(self) -> None:
        assert PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_FIX == "FIX 364"
        assert PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ID == "PHASE_J1"
        assert PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_SCHEMA_VERSION == (
            "phase_production_reality_longitudinal_operations_program_v1"
        )
        assert OPERATIONAL_AUTHORITY_FIX_364 is False
        assert AUTONOMOUS_PRODUCTION_CONTROL_FIX_364 is False
        assert AUTHORITY_EXPANSION_FIX_364 is False
        assert GOVERNANCE_MUTATION_FIX_364 is False
        assert GOVERNANCE_BYPASS_FIX_364 is False
        assert TRUST_PROMOTION_FIX_364 is False
        assert APPROVAL_BYPASS_FIX_364 is False
        assert OPERATIONAL_AUTOMATION_CHANGES_FIX_364 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_364 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_364 is False
        assert LOCAL_PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_EXECUTABLE_FIX_364 is True

    def test_fix_364_measurement_not_operational_authority(self) -> None:
        board = build_production_reality_longitudinal_operations_program(
            session_id=SESSION
        ).production_reality_longitudinal_operations_program
        assert set(board["fix_364_certification_requirements"]) == set(FIX_364_CERTIFICATION_REQUIREMENTS)
        assert board["operational_authority"] is False
        assert "operational_authority" in PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_INVARIANT

    def test_fix_364_phases_present(self) -> None:
        sections = build_production_reality_longitudinal_operations_program(
            session_id=SESSION
        ).production_reality_longitudinal_operations_program["sections"]
        for phase in PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PHASES:
            assert sections[phase]

    def test_fix_364_certification_requirement_count(self) -> None:
        assert len(FIX_364_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_364_route_id(self) -> None:
        assert PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ROUTE_ID == (
            "phase_production_reality_longitudinal_operations_program"
        )
