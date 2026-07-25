# SPDX-License-Identifier: Apache-2.0
"""FIX 355 / WORKSTREAM_G2 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_355_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_contract import (
    AUTHORITY_EXPANSION_FIX_355,
    AUTOMATED_OUTREACH_FIX_355,
    BEHAVIORAL_MANIPULATION_FIX_355,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_355,
    LOCAL_USAGE_ADOPTION_EXECUTABLE_FIX_355,
    PLAN_MUTATION_FIX_355,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PHASES,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_FIX,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ID,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_INVARIANT,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ROUTE_ID,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_355,
    TRUST_MUTATION_FIX_355,
    USER_AUTHORITY_FIX_355,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_service import (
    build_real_usage_density_platform_adoption_program,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_store import (
    clear_platform_adoption_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-g2-cert-355"


@pytest.fixture(autouse=True)
def _clean():
    clear_platform_adoption_records_for_tests()
    yield
    clear_platform_adoption_records_for_tests()


class TestWorkstreamG2RealUsageDensityPlatformAdoptionCertification:
    def test_fix_355_contract(self) -> None:
        assert REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_FIX == "FIX 355"
        assert REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ID == "WORKSTREAM_G2"
        assert REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_SCHEMA_VERSION == (
            "workstream_real_usage_density_platform_adoption_program_v1"
        )
        assert USER_AUTHORITY_FIX_355 is False
        assert AUTOMATED_OUTREACH_FIX_355 is False
        assert BEHAVIORAL_MANIPULATION_FIX_355 is False
        assert PLAN_MUTATION_FIX_355 is False
        assert TRUST_MUTATION_FIX_355 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_355 is False
        assert AUTHORITY_EXPANSION_FIX_355 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_355 is False
        assert LOCAL_USAGE_ADOPTION_EXECUTABLE_FIX_355 is True

    def test_fix_355_usage_not_user_authority(self) -> None:
        board = build_real_usage_density_platform_adoption_program(
            session_id=SESSION
        ).real_usage_density_platform_adoption_program
        assert set(board["fix_355_certification_requirements"]) == set(FIX_355_CERTIFICATION_REQUIREMENTS)
        assert board["user_authority"] is False
        assert "user_authority" in REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_INVARIANT

    def test_fix_355_phases_present(self) -> None:
        sections = build_real_usage_density_platform_adoption_program(
            session_id=SESSION
        ).real_usage_density_platform_adoption_program["sections"]
        for phase in REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PHASES:
            assert sections[phase]

    def test_fix_355_certification_requirement_count(self) -> None:
        assert len(FIX_355_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_355_route_id(self) -> None:
        assert REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ROUTE_ID == (
            "workstream_real_usage_density_platform_adoption_program"
        )
