# SPDX-License-Identifier: Apache-2.0
"""FIX 348 / WORKSTREAM_F2 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_348_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_348,
    AUTOMATED_OUTREACH_FIX_348,
    CUSTOMER_MANIPULATION_FIX_348,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PHASES,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_FIX,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ID,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_INVARIANT,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ROUTE_ID,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_SCHEMA_VERSION,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_348,
    LOCAL_VALUE_VALIDATION_EXECUTABLE_FIX_348,
    TRUST_MUTATION_AUTHORITY_FIX_348,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_service import (
    build_customer_value_adoption_validation_program,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    clear_customer_value_adoption_validation_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-f2-cert-348"


@pytest.fixture(autouse=True)
def _clean():
    clear_customer_value_adoption_validation_records_for_tests()
    yield
    clear_customer_value_adoption_validation_records_for_tests()


class TestWorkstreamF2CustomerValueAdoptionValidationCertification:
    def test_fix_348_contract(self) -> None:
        assert CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_FIX == "FIX 348"
        assert CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ID == "WORKSTREAM_F2"
        assert CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_SCHEMA_VERSION == (
            "workstream_customer_value_adoption_validation_program_v1"
        )
        assert CUSTOMER_MANIPULATION_FIX_348 is False
        assert AUTOMATED_OUTREACH_FIX_348 is False
        assert AUTHORITY_EXPANSION_FIX_348 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_348 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_348 is False
        assert LOCAL_VALUE_VALIDATION_EXECUTABLE_FIX_348 is True

    def test_fix_348_validation_not_manipulation(self) -> None:
        board = build_customer_value_adoption_validation_program(
            session_id=SESSION
        ).customer_value_adoption_validation_program
        assert set(board["fix_348_certification_requirements"]) == set(FIX_348_CERTIFICATION_REQUIREMENTS)
        assert board["customer_manipulation"] is False
        assert "manipulation" in CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_INVARIANT

    def test_fix_348_phases_present(self) -> None:
        sections = build_customer_value_adoption_validation_program(
            session_id=SESSION
        ).customer_value_adoption_validation_program["sections"]
        for phase in CUSTOMER_VALUE_ADOPTION_VALIDATION_PHASES:
            assert sections[phase]

    def test_fix_348_certification_requirement_count(self) -> None:
        assert len(FIX_348_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_348_route_id(self) -> None:
        assert CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ROUTE_ID == (
            "workstream_customer_value_adoption_validation_program"
        )
