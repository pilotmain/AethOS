# SPDX-License-Identifier: Apache-2.0
"""FIX 349 / WORKSTREAM_F3 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_349_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_contract import (
    AUTHORITY_EXPANSION_FIX_349,
    AUTOMATED_OUTREACH_FIX_349,
    CUSTOMER_AUTHORITY_FIX_349,
    CUSTOMER_MANIPULATION_FIX_349,
    MULTI_CUSTOMER_VALUE_PROOF_PHASES,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_FIX,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ID,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_INVARIANT,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ROUTE_ID,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_SCHEMA_VERSION,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_349,
    LOCAL_MULTI_CUSTOMER_PROOF_EXECUTABLE_FIX_349,
    TRUST_MUTATION_AUTHORITY_FIX_349,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_service import (
    build_multi_customer_value_proof_program,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_store import (
    clear_multi_customer_value_proof_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-f3-cert-349"


@pytest.fixture(autouse=True)
def _clean():
    clear_multi_customer_value_proof_records_for_tests()
    yield
    clear_multi_customer_value_proof_records_for_tests()


class TestWorkstreamF3MultiCustomerValueProofCertification:
    def test_fix_349_contract(self) -> None:
        assert MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_FIX == "FIX 349"
        assert MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ID == "WORKSTREAM_F3"
        assert MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_SCHEMA_VERSION == (
            "workstream_multi_customer_value_proof_program_v1"
        )
        assert CUSTOMER_AUTHORITY_FIX_349 is False
        assert CUSTOMER_MANIPULATION_FIX_349 is False
        assert AUTOMATED_OUTREACH_FIX_349 is False
        assert AUTHORITY_EXPANSION_FIX_349 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_349 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_349 is False
        assert LOCAL_MULTI_CUSTOMER_PROOF_EXECUTABLE_FIX_349 is True

    def test_fix_349_proof_not_customer_authority(self) -> None:
        board = build_multi_customer_value_proof_program(
            session_id=SESSION
        ).multi_customer_value_proof_program
        assert set(board["fix_349_certification_requirements"]) == set(FIX_349_CERTIFICATION_REQUIREMENTS)
        assert board["customer_authority"] is False
        assert "customer_authority" in MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_INVARIANT

    def test_fix_349_phases_present(self) -> None:
        sections = build_multi_customer_value_proof_program(
            session_id=SESSION
        ).multi_customer_value_proof_program["sections"]
        for phase in MULTI_CUSTOMER_VALUE_PROOF_PHASES:
            assert sections[phase]

    def test_fix_349_certification_requirement_count(self) -> None:
        assert len(FIX_349_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_349_route_id(self) -> None:
        assert MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ROUTE_ID == "workstream_multi_customer_value_proof_program"
