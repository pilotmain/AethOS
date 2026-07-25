# SPDX-License-Identifier: Apache-2.0
"""FIX 339 / WORKSTREAM_C1 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_339_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_contract import (
    AUTHORITY_EXPANSION_FIX_339,
    DELIVERY_AUTHORITY_FIX_339,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_339,
    LOCAL_DELIVERY_PROOF_EXECUTABLE_FIX_339,
    REAL_WORLD_DELIVERY_PROOF_PHASES,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_FIX,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_ID,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_INVARIANT,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_ROUTE_ID,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_339,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_service import (
    build_real_world_delivery_proof_program,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_store import (
    clear_real_world_delivery_proof_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-c1-cert-339"


@pytest.fixture(autouse=True)
def _clean():
    clear_real_world_delivery_proof_records_for_tests()
    yield
    clear_real_world_delivery_proof_records_for_tests()


class TestWorkstreamC1RealWorldDeliveryProofProgramCertification:
    def test_fix_339_contract(self) -> None:
        assert REAL_WORLD_DELIVERY_PROOF_PROGRAM_FIX == "FIX 339"
        assert REAL_WORLD_DELIVERY_PROOF_PROGRAM_ID == "WORKSTREAM_C1"
        assert REAL_WORLD_DELIVERY_PROOF_PROGRAM_SCHEMA_VERSION == (
            "workstream_real_world_delivery_proof_program_v1"
        )
        assert DELIVERY_AUTHORITY_FIX_339 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_339 is False
        assert AUTHORITY_EXPANSION_FIX_339 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_339 is False
        assert LOCAL_DELIVERY_PROOF_EXECUTABLE_FIX_339 is True

    def test_fix_339_proof_not_authority(self) -> None:
        result = build_real_world_delivery_proof_program(session_id=SESSION)
        board = result.real_world_delivery_proof_program
        assert set(board["fix_339_certification_requirements"]) == set(FIX_339_CERTIFICATION_REQUIREMENTS)
        assert board["delivery_authority"] is False
        assert "authority" in REAL_WORLD_DELIVERY_PROOF_PROGRAM_INVARIANT

    def test_fix_339_phases_present(self) -> None:
        result = build_real_world_delivery_proof_program(session_id=SESSION)
        sections = result.real_world_delivery_proof_program["sections"]
        for phase in REAL_WORLD_DELIVERY_PROOF_PHASES:
            assert sections[phase]

    def test_fix_339_certification_requirement_count(self) -> None:
        assert len(FIX_339_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_339_route_id(self) -> None:
        assert REAL_WORLD_DELIVERY_PROOF_PROGRAM_ROUTE_ID == "workstream_real_world_delivery_proof_program"
