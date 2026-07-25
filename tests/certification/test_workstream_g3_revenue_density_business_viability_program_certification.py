# SPDX-License-Identifier: Apache-2.0
"""FIX 356 / WORKSTREAM_G3 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_356_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_contract import (
    AUTHORITY_EXPANSION_FIX_356,
    BILLING_EXECUTION_FIX_356,
    COMMERCIAL_AUTHORITY_FIX_356,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_356,
    LOCAL_REVENUE_DENSITY_EXECUTABLE_FIX_356,
    PAYMENT_PROCESSING_FIX_356,
    PLAN_UPGRADE_FIX_356,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PHASES,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_FIX,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ID,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_INVARIANT,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ROUTE_ID,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_SCHEMA_VERSION,
    SUBSCRIPTION_MUTATION_FIX_356,
    TRUST_MUTATION_AUTHORITY_FIX_356,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_service import (
    build_revenue_density_business_viability_program,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_store import (
    clear_revenue_density_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-g3-cert-356"


@pytest.fixture(autouse=True)
def _clean():
    clear_revenue_density_records_for_tests()
    yield
    clear_revenue_density_records_for_tests()


class TestWorkstreamG3RevenueDensityBusinessViabilityCertification:
    def test_fix_356_contract(self) -> None:
        assert REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_FIX == "FIX 356"
        assert REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ID == "WORKSTREAM_G3"
        assert REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_SCHEMA_VERSION == (
            "workstream_revenue_density_business_viability_program_v1"
        )
        assert COMMERCIAL_AUTHORITY_FIX_356 is False
        assert PAYMENT_PROCESSING_FIX_356 is False
        assert BILLING_EXECUTION_FIX_356 is False
        assert SUBSCRIPTION_MUTATION_FIX_356 is False
        assert PLAN_UPGRADE_FIX_356 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_356 is False
        assert AUTHORITY_EXPANSION_FIX_356 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_356 is False
        assert LOCAL_REVENUE_DENSITY_EXECUTABLE_FIX_356 is True

    def test_fix_356_revenue_not_commercial_authority(self) -> None:
        board = build_revenue_density_business_viability_program(
            session_id=SESSION
        ).revenue_density_business_viability_program
        assert set(board["fix_356_certification_requirements"]) == set(FIX_356_CERTIFICATION_REQUIREMENTS)
        assert board["commercial_authority"] is False
        assert "commercial_authority" in REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_INVARIANT

    def test_fix_356_phases_present(self) -> None:
        sections = build_revenue_density_business_viability_program(
            session_id=SESSION
        ).revenue_density_business_viability_program["sections"]
        for phase in REVENUE_DENSITY_BUSINESS_VIABILITY_PHASES:
            assert sections[phase]

    def test_fix_356_certification_requirement_count(self) -> None:
        assert len(FIX_356_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_356_route_id(self) -> None:
        assert REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ROUTE_ID == (
            "workstream_revenue_density_business_viability_program"
        )
