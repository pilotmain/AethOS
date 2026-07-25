# SPDX-License-Identifier: Apache-2.0
"""FIX 342 / WORKSTREAM_D2 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_342_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_contract import (
    AUTHORITY_EXPANSION_FIX_342,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_342,
    LOCAL_MULTI_CLOUD_PROOF_EXECUTABLE_FIX_342,
    MULTI_CLOUD_OPERATIONAL_PROOF_PHASES,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_FIX,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ID,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_INVARIANT,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ROUTE_ID,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION,
    PROVIDER_AUTHORITY_FIX_342,
    TRUST_MUTATION_AUTHORITY_FIX_342,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_service import (
    build_multi_cloud_operational_proof_program,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_store import (
    clear_multi_cloud_operational_proof_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-d2-cert-342"


@pytest.fixture(autouse=True)
def _clean():
    clear_multi_cloud_operational_proof_records_for_tests()
    yield
    clear_multi_cloud_operational_proof_records_for_tests()


class TestWorkstreamD2MultiCloudOperationalProofCertification:
    def test_fix_342_contract(self) -> None:
        assert MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_FIX == "FIX 342"
        assert MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ID == "WORKSTREAM_D2"
        assert MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION == (
            "workstream_multi_cloud_operational_proof_program_v1"
        )
        assert PROVIDER_AUTHORITY_FIX_342 is False
        assert AUTHORITY_EXPANSION_FIX_342 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_342 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_342 is False
        assert LOCAL_MULTI_CLOUD_PROOF_EXECUTABLE_FIX_342 is True

    def test_fix_342_proof_not_authority(self) -> None:
        board = build_multi_cloud_operational_proof_program(session_id=SESSION).multi_cloud_operational_proof_program
        assert set(board["fix_342_certification_requirements"]) == set(FIX_342_CERTIFICATION_REQUIREMENTS)
        assert board["provider_authority"] is False
        assert board["authority_expansion"] is False
        assert "provider_authority" in MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_INVARIANT

    def test_fix_342_phases_present(self) -> None:
        sections = build_multi_cloud_operational_proof_program(session_id=SESSION).multi_cloud_operational_proof_program[
            "sections"
        ]
        for phase in MULTI_CLOUD_OPERATIONAL_PROOF_PHASES:
            assert sections[phase]

    def test_fix_342_certification_requirement_count(self) -> None:
        assert len(FIX_342_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_342_route_id(self) -> None:
        assert MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ROUTE_ID == (
            "workstream_multi_cloud_operational_proof_program"
        )
