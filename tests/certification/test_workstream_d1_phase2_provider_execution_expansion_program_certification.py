# SPDX-License-Identifier: Apache-2.0
"""FIX 341 / WORKSTREAM_D1 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_341_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_contract import (
    AUTHORITY_EXPANSION_FIX_341,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_341,
    LOCAL_PHASE2_EXECUTION_EXECUTABLE_FIX_341,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PHASES,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_FIX,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ID,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_INVARIANT,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ROUTE_ID,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_SCHEMA_VERSION,
    ROLLBACK_EXECUTION_AUTHORITY_FIX_341,
    SPECIAL_PROVIDER_AUTHORITY_FIX_341,
    TRUST_MUTATION_AUTHORITY_FIX_341,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_service import (
    build_phase2_provider_execution_expansion_program,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_store import (
    clear_phase2_provider_execution_expansion_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-d1-cert-341"


@pytest.fixture(autouse=True)
def _clean():
    clear_phase2_provider_execution_expansion_records_for_tests()
    yield
    clear_phase2_provider_execution_expansion_records_for_tests()


class TestWorkstreamD1Phase2ProviderExecutionExpansionCertification:
    def test_fix_341_contract(self) -> None:
        assert PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_FIX == "FIX 341"
        assert PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ID == "WORKSTREAM_D1"
        assert PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_SCHEMA_VERSION == (
            "workstream_phase2_provider_execution_expansion_program_v1"
        )
        assert AUTHORITY_EXPANSION_FIX_341 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_341 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_341 is False
        assert SPECIAL_PROVIDER_AUTHORITY_FIX_341 is False
        assert ROLLBACK_EXECUTION_AUTHORITY_FIX_341 is False
        assert LOCAL_PHASE2_EXECUTION_EXECUTABLE_FIX_341 is True

    def test_fix_341_expansion_not_authority(self) -> None:
        board = build_phase2_provider_execution_expansion_program(session_id=SESSION).phase2_provider_execution_expansion_program
        assert set(board["fix_341_certification_requirements"]) == set(FIX_341_CERTIFICATION_REQUIREMENTS)
        assert board["authority_expansion"] is False
        assert "authority" in PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_INVARIANT

    def test_fix_341_phases_present(self) -> None:
        sections = build_phase2_provider_execution_expansion_program(session_id=SESSION).phase2_provider_execution_expansion_program["sections"]
        for phase in PHASE2_PROVIDER_EXECUTION_EXPANSION_PHASES:
            assert sections[phase]

    def test_fix_341_certification_requirement_count(self) -> None:
        assert len(FIX_341_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_341_route_id(self) -> None:
        assert PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ROUTE_ID == (
            "workstream_phase2_provider_execution_expansion_program"
        )
