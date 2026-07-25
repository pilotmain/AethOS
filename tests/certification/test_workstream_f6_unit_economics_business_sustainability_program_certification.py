# SPDX-License-Identifier: Apache-2.0
"""FIX 352 / WORKSTREAM_F6 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_352_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_contract import (
    AUTHORITY_EXPANSION_FIX_352,
    BILLING_EXECUTION_FIX_352,
    COMMERCIAL_AUTHORITY_FIX_352,
    FINANCIAL_FORECASTING_AS_FACT_FIX_352,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_352,
    LOCAL_ECONOMIC_VALIDATION_EXECUTABLE_FIX_352,
    PAYMENT_PROCESSING_FIX_352,
    TRUST_MUTATION_AUTHORITY_FIX_352,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PHASES,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_FIX,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ID,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_INVARIANT,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ROUTE_ID,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_SCHEMA_VERSION,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_service import (
    build_unit_economics_business_sustainability_program,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_store import (
    clear_business_sustainability_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-f6-cert-352"


@pytest.fixture(autouse=True)
def _clean():
    clear_business_sustainability_records_for_tests()
    yield
    clear_business_sustainability_records_for_tests()


class TestWorkstreamF6UnitEconomicsBusinessSustainabilityCertification:
    def test_fix_352_contract(self) -> None:
        assert UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_FIX == "FIX 352"
        assert UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ID == "WORKSTREAM_F6"
        assert UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_SCHEMA_VERSION == (
            "workstream_unit_economics_business_sustainability_program_v1"
        )
        assert COMMERCIAL_AUTHORITY_FIX_352 is False
        assert PAYMENT_PROCESSING_FIX_352 is False
        assert BILLING_EXECUTION_FIX_352 is False
        assert FINANCIAL_FORECASTING_AS_FACT_FIX_352 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_352 is False
        assert AUTHORITY_EXPANSION_FIX_352 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_352 is False
        assert LOCAL_ECONOMIC_VALIDATION_EXECUTABLE_FIX_352 is True

    def test_fix_352_economic_not_commercial_authority(self) -> None:
        board = build_unit_economics_business_sustainability_program(
            session_id=SESSION
        ).unit_economics_business_sustainability_program
        assert set(board["fix_352_certification_requirements"]) == set(FIX_352_CERTIFICATION_REQUIREMENTS)
        assert board["commercial_authority"] is False
        assert "commercial_authority" in UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_INVARIANT

    def test_fix_352_phases_present(self) -> None:
        sections = build_unit_economics_business_sustainability_program(
            session_id=SESSION
        ).unit_economics_business_sustainability_program["sections"]
        for phase in UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PHASES:
            assert sections[phase]

    def test_fix_352_certification_requirement_count(self) -> None:
        assert len(FIX_352_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_352_route_id(self) -> None:
        assert UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ROUTE_ID == (
            "workstream_unit_economics_business_sustainability_program"
        )
