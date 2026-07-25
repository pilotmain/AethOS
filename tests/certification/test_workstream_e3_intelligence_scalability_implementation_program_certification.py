# SPDX-License-Identifier: Apache-2.0
"""FIX 345 / WORKSTREAM_E3 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_345_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_contract import (
    AUTHORITY_EXPANSION_FIX_345,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_345,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PHASES,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_FIX,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ID,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_INVARIANT,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ROUTE_ID,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_SCHEMA_VERSION,
    LOCAL_SCALABILITY_IMPLEMENTATION_EXECUTABLE_FIX_345,
    TRUST_MUTATION_AUTHORITY_FIX_345,
    TRUTH_MUTATION_FIX_345,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_service import (
    build_intelligence_scalability_implementation_program,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_store import (
    clear_intelligence_scalability_implementation_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-e3-cert-345"


@pytest.fixture(autouse=True)
def _clean():
    clear_intelligence_scalability_implementation_records_for_tests()
    yield
    clear_intelligence_scalability_implementation_records_for_tests()


class TestWorkstreamE3IntelligenceScalabilityImplementationCertification:
    def test_fix_345_contract(self) -> None:
        assert INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_FIX == "FIX 345"
        assert INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ID == "WORKSTREAM_E3"
        assert INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_SCHEMA_VERSION == (
            "workstream_intelligence_scalability_implementation_program_v1"
        )
        assert TRUTH_MUTATION_FIX_345 is False
        assert AUTHORITY_EXPANSION_FIX_345 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_345 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_345 is False
        assert LOCAL_SCALABILITY_IMPLEMENTATION_EXECUTABLE_FIX_345 is True

    def test_fix_345_execution_not_truth_mutation(self) -> None:
        board = build_intelligence_scalability_implementation_program(
            session_id=SESSION
        ).intelligence_scalability_implementation_program
        assert set(board["fix_345_certification_requirements"]) == set(FIX_345_CERTIFICATION_REQUIREMENTS)
        assert board["truth_mutation"] is False
        assert "truth_mutation" in INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_INVARIANT

    def test_fix_345_phases_present(self) -> None:
        sections = build_intelligence_scalability_implementation_program(
            session_id=SESSION
        ).intelligence_scalability_implementation_program["sections"]
        for phase in INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PHASES:
            assert sections[phase]

    def test_fix_345_certification_requirement_count(self) -> None:
        assert len(FIX_345_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_345_route_id(self) -> None:
        assert INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ROUTE_ID == (
            "workstream_intelligence_scalability_implementation_program"
        )
