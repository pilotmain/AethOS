# SPDX-License-Identifier: Apache-2.0
"""FIX 350 / WORKSTREAM_F4 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_350_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_350,
    AUTOMATED_OUTREACH_FIX_350,
    CUSTOMER_AUTHORITY_FIX_350,
    CUSTOMER_MANIPULATION_FIX_350,
    CUSTOMER_SCALE_VALIDATION_PHASES,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_FIX,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_ID,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_INVARIANT,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_ROUTE_ID,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_SCHEMA_VERSION,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_350,
    LOCAL_SCALE_VALIDATION_EXECUTABLE_FIX_350,
    TRUST_MUTATION_AUTHORITY_FIX_350,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_service import (
    build_customer_scale_validation_program,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_store import (
    clear_customer_scale_validation_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-f4-cert-350"


@pytest.fixture(autouse=True)
def _clean():
    clear_customer_scale_validation_records_for_tests()
    yield
    clear_customer_scale_validation_records_for_tests()


class TestWorkstreamF4CustomerScaleValidationCertification:
    def test_fix_350_contract(self) -> None:
        assert CUSTOMER_SCALE_VALIDATION_PROGRAM_FIX == "FIX 350"
        assert CUSTOMER_SCALE_VALIDATION_PROGRAM_ID == "WORKSTREAM_F4"
        assert CUSTOMER_SCALE_VALIDATION_PROGRAM_SCHEMA_VERSION == (
            "workstream_customer_scale_validation_program_v1"
        )
        assert CUSTOMER_AUTHORITY_FIX_350 is False
        assert CUSTOMER_MANIPULATION_FIX_350 is False
        assert AUTOMATED_OUTREACH_FIX_350 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_350 is False
        assert AUTHORITY_EXPANSION_FIX_350 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_350 is False
        assert LOCAL_SCALE_VALIDATION_EXECUTABLE_FIX_350 is True

    def test_fix_350_scale_not_customer_authority(self) -> None:
        board = build_customer_scale_validation_program(
            session_id=SESSION
        ).customer_scale_validation_program
        assert set(board["fix_350_certification_requirements"]) == set(FIX_350_CERTIFICATION_REQUIREMENTS)
        assert board["customer_authority"] is False
        assert "customer_authority" in CUSTOMER_SCALE_VALIDATION_PROGRAM_INVARIANT

    def test_fix_350_phases_present(self) -> None:
        sections = build_customer_scale_validation_program(
            session_id=SESSION
        ).customer_scale_validation_program["sections"]
        for phase in CUSTOMER_SCALE_VALIDATION_PHASES:
            assert sections[phase]

    def test_fix_350_certification_requirement_count(self) -> None:
        assert len(FIX_350_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_350_route_id(self) -> None:
        assert CUSTOMER_SCALE_VALIDATION_PROGRAM_ROUTE_ID == "workstream_customer_scale_validation_program"
