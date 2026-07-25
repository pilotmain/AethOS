# SPDX-License-Identifier: Apache-2.0
"""FIX 353 / WORKSTREAM_F7 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_353_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_353,
    BUSINESS_AUTOMATION_FIX_353,
    BUSINESS_OPERATING_MODEL_VALIDATION_PHASES,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_FIX,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ID,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_INVARIANT,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ROUTE_ID,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_SCHEMA_VERSION,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_353,
    GOVERNANCE_MUTATION_FIX_353,
    LOCAL_OPERATING_MODEL_VALIDATION_EXECUTABLE_FIX_353,
    OPERATING_AUTHORITY_FIX_353,
    PROVIDER_MUTATION_FIX_353,
    TRUST_MUTATION_AUTHORITY_FIX_353,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_service import (
    build_business_operating_model_validation_program,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_store import (
    clear_operating_model_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-f7-cert-353"


@pytest.fixture(autouse=True)
def _clean():
    clear_operating_model_records_for_tests()
    yield
    clear_operating_model_records_for_tests()


class TestWorkstreamF7BusinessOperatingModelValidationCertification:
    def test_fix_353_contract(self) -> None:
        assert BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_FIX == "FIX 353"
        assert BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ID == "WORKSTREAM_F7"
        assert BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_SCHEMA_VERSION == (
            "workstream_business_operating_model_validation_program_v1"
        )
        assert OPERATING_AUTHORITY_FIX_353 is False
        assert GOVERNANCE_MUTATION_FIX_353 is False
        assert PROVIDER_MUTATION_FIX_353 is False
        assert BUSINESS_AUTOMATION_FIX_353 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_353 is False
        assert AUTHORITY_EXPANSION_FIX_353 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_353 is False
        assert LOCAL_OPERATING_MODEL_VALIDATION_EXECUTABLE_FIX_353 is True

    def test_fix_353_operating_not_authority(self) -> None:
        board = build_business_operating_model_validation_program(
            session_id=SESSION
        ).business_operating_model_validation_program
        assert set(board["fix_353_certification_requirements"]) == set(FIX_353_CERTIFICATION_REQUIREMENTS)
        assert board["operating_authority"] is False
        assert "operating_authority" in BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_INVARIANT

    def test_fix_353_phases_present(self) -> None:
        sections = build_business_operating_model_validation_program(
            session_id=SESSION
        ).business_operating_model_validation_program["sections"]
        for phase in BUSINESS_OPERATING_MODEL_VALIDATION_PHASES:
            assert sections[phase]

    def test_fix_353_certification_requirement_count(self) -> None:
        assert len(FIX_353_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_353_route_id(self) -> None:
        assert BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ROUTE_ID == (
            "workstream_business_operating_model_validation_program"
        )
