# SPDX-License-Identifier: Apache-2.0
"""FIX 357 / WORKSTREAM_G4 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_357_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_contract import (
    AUTHORITY_EXPANSION_FIX_357,
    BUSINESS_AUTOMATION_FIX_357,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PHASES,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_FIX,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ID,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_INVARIANT,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ROUTE_ID,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_SCHEMA_VERSION,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_357,
    GOVERNANCE_MUTATION_FIX_357,
    LAUNCH_AUTHORITY_FIX_357,
    LOCAL_PLATFORM_MATURITY_EXECUTABLE_FIX_357,
    TRUST_MUTATION_AUTHORITY_FIX_357,
    TRUST_PROMOTION_FIX_357,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_service import (
    build_enterprise_platform_maturity_readiness_audit_program,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_store import (
    clear_platform_maturity_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-g4-cert-357"


@pytest.fixture(autouse=True)
def _clean():
    clear_platform_maturity_records_for_tests()
    yield
    clear_platform_maturity_records_for_tests()


class TestWorkstreamG4EnterprisePlatformMaturityReadinessCertification:
    def test_fix_357_contract(self) -> None:
        assert ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_FIX == "FIX 357"
        assert ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ID == "WORKSTREAM_G4"
        assert ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_SCHEMA_VERSION == (
            "workstream_enterprise_platform_maturity_readiness_audit_program_v1"
        )
        assert LAUNCH_AUTHORITY_FIX_357 is False
        assert AUTHORITY_EXPANSION_FIX_357 is False
        assert GOVERNANCE_MUTATION_FIX_357 is False
        assert TRUST_PROMOTION_FIX_357 is False
        assert BUSINESS_AUTOMATION_FIX_357 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_357 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_357 is False
        assert LOCAL_PLATFORM_MATURITY_EXECUTABLE_FIX_357 is True

    def test_fix_357_maturity_not_launch_authority(self) -> None:
        board = build_enterprise_platform_maturity_readiness_audit_program(
            session_id=SESSION
        ).enterprise_platform_maturity_readiness_audit_program
        assert set(board["fix_357_certification_requirements"]) == set(FIX_357_CERTIFICATION_REQUIREMENTS)
        assert board["launch_authority"] is False
        assert "launch_authority" in ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_INVARIANT

    def test_fix_357_phases_present(self) -> None:
        sections = build_enterprise_platform_maturity_readiness_audit_program(
            session_id=SESSION
        ).enterprise_platform_maturity_readiness_audit_program["sections"]
        for phase in ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PHASES:
            assert sections[phase]

    def test_fix_357_certification_requirement_count(self) -> None:
        assert len(FIX_357_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_357_route_id(self) -> None:
        assert ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ROUTE_ID == (
            "workstream_enterprise_platform_maturity_readiness_audit_program"
        )
