# SPDX-License-Identifier: Apache-2.0
"""FIX 351 / WORKSTREAM_F5 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_351_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_351,
    AUTOMATIC_PLAN_UPGRADE_FIX_351,
    COMMERCIAL_AUTHORITY_FIX_351,
    COMMERCIAL_VALIDATION_PHASES,
    COMMERCIAL_VALIDATION_PROGRAM_FIX,
    COMMERCIAL_VALIDATION_PROGRAM_ID,
    COMMERCIAL_VALIDATION_PROGRAM_INVARIANT,
    COMMERCIAL_VALIDATION_PROGRAM_ROUTE_ID,
    COMMERCIAL_VALIDATION_PROGRAM_SCHEMA_VERSION,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_351,
    LOCAL_COMMERCIAL_VALIDATION_EXECUTABLE_FIX_351,
    PAYMENT_PROCESSING_FIX_351,
    TRUST_MUTATION_AUTHORITY_FIX_351,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_service import (
    build_commercial_validation_program,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_store import (
    clear_commercial_validation_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-f5-cert-351"


@pytest.fixture(autouse=True)
def _clean():
    clear_commercial_validation_records_for_tests()
    yield
    clear_commercial_validation_records_for_tests()


class TestWorkstreamF5CommercialValidationCertification:
    def test_fix_351_contract(self) -> None:
        assert COMMERCIAL_VALIDATION_PROGRAM_FIX == "FIX 351"
        assert COMMERCIAL_VALIDATION_PROGRAM_ID == "WORKSTREAM_F5"
        assert COMMERCIAL_VALIDATION_PROGRAM_SCHEMA_VERSION == "workstream_commercial_validation_program_v1"
        assert COMMERCIAL_AUTHORITY_FIX_351 is False
        assert PAYMENT_PROCESSING_FIX_351 is False
        assert AUTOMATIC_PLAN_UPGRADE_FIX_351 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_351 is False
        assert AUTHORITY_EXPANSION_FIX_351 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_351 is False
        assert LOCAL_COMMERCIAL_VALIDATION_EXECUTABLE_FIX_351 is True

    def test_fix_351_commercial_not_authority(self) -> None:
        board = build_commercial_validation_program(session_id=SESSION).commercial_validation_program
        assert set(board["fix_351_certification_requirements"]) == set(FIX_351_CERTIFICATION_REQUIREMENTS)
        assert board["commercial_authority"] is False
        assert "commercial_authority" in COMMERCIAL_VALIDATION_PROGRAM_INVARIANT

    def test_fix_351_phases_present(self) -> None:
        sections = build_commercial_validation_program(session_id=SESSION).commercial_validation_program["sections"]
        for phase in COMMERCIAL_VALIDATION_PHASES:
            assert sections[phase]

    def test_fix_351_certification_requirement_count(self) -> None:
        assert len(FIX_351_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_351_route_id(self) -> None:
        assert COMMERCIAL_VALIDATION_PROGRAM_ROUTE_ID == "workstream_commercial_validation_program"
