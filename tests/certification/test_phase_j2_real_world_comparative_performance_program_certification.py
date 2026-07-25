# SPDX-License-Identifier: Apache-2.0
"""FIX 365 / PHASE_J2 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_365_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_contract import (
    AUTHORITY_EXPANSION_FIX_365,
    COMPETITIVE_ACTIONS_FIX_365,
    COMPETITIVE_AUTHORITY_FIX_365,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_365,
    GOVERNANCE_BYPASS_FIX_365,
    GOVERNANCE_MUTATION_FIX_365,
    LOCAL_REAL_WORLD_COMPARATIVE_PERFORMANCE_EXECUTABLE_FIX_365,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PHASES,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_FIX,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_INVARIANT,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ROUTE_ID,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_SCHEMA_VERSION,
    STRATEGY_MUTATION_FIX_365,
    TRUST_MUTATION_AUTHORITY_FIX_365,
    TRUST_PROMOTION_FIX_365,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_service import (
    build_real_world_comparative_performance_program,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_store import (
    clear_comparative_performance_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-j2-cert-365"


@pytest.fixture(autouse=True)
def _clean():
    clear_comparative_performance_records_for_tests()
    yield
    clear_comparative_performance_records_for_tests()


class TestPhaseJ2RealWorldComparativePerformanceCertification:
    def test_fix_365_contract(self) -> None:
        assert REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_FIX == "FIX 365"
        assert REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID == "PHASE_J2"
        assert REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_SCHEMA_VERSION == (
            "phase_real_world_comparative_performance_program_v1"
        )
        assert COMPETITIVE_AUTHORITY_FIX_365 is False
        assert COMPETITIVE_ACTIONS_FIX_365 is False
        assert STRATEGY_MUTATION_FIX_365 is False
        assert AUTHORITY_EXPANSION_FIX_365 is False
        assert GOVERNANCE_MUTATION_FIX_365 is False
        assert GOVERNANCE_BYPASS_FIX_365 is False
        assert TRUST_PROMOTION_FIX_365 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_365 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_365 is False
        assert LOCAL_REAL_WORLD_COMPARATIVE_PERFORMANCE_EXECUTABLE_FIX_365 is True

    def test_fix_365_comparison_not_competitive_authority(self) -> None:
        board = build_real_world_comparative_performance_program(
            session_id=SESSION
        ).real_world_comparative_performance_program
        assert set(board["fix_365_certification_requirements"]) == set(FIX_365_CERTIFICATION_REQUIREMENTS)
        assert board["competitive_authority"] is False
        assert "competitive_authority" in REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_INVARIANT

    def test_fix_365_phases_present(self) -> None:
        sections = build_real_world_comparative_performance_program(
            session_id=SESSION
        ).real_world_comparative_performance_program["sections"]
        for phase in REAL_WORLD_COMPARATIVE_PERFORMANCE_PHASES:
            assert sections[phase]

    def test_fix_365_certification_requirement_count(self) -> None:
        assert len(FIX_365_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_365_route_id(self) -> None:
        assert REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ROUTE_ID == (
            "phase_real_world_comparative_performance_program"
        )
