# SPDX-License-Identifier: Apache-2.0
"""FIX 343 / WORKSTREAM_E1 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_343_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_contract import (
    AUTHORITY_EXPANSION_FIX_343,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_343,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_FIX,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ID,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_INVARIANT,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ROUTE_ID,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_SCHEMA_VERSION,
    INTELLIGENCE_PERFORMANCE_PHASES,
    LOCAL_PERFORMANCE_ANALYSIS_EXECUTABLE_FIX_343,
    TRUST_MUTATION_AUTHORITY_FIX_343,
    TRUTH_REDUCTION_FIX_343,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_service import (
    build_intelligence_performance_evidence_scalability_program,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_store import (
    clear_intelligence_performance_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-e1-cert-343"


@pytest.fixture(autouse=True)
def _clean():
    clear_intelligence_performance_records_for_tests()
    yield
    clear_intelligence_performance_records_for_tests()


class TestWorkstreamE1IntelligencePerformanceCertification:
    def test_fix_343_contract(self) -> None:
        assert INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_FIX == "FIX 343"
        assert INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ID == "WORKSTREAM_E1"
        assert INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_SCHEMA_VERSION == (
            "workstream_intelligence_performance_evidence_scalability_program_v1"
        )
        assert TRUTH_REDUCTION_FIX_343 is False
        assert AUTHORITY_EXPANSION_FIX_343 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_343 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_343 is False
        assert LOCAL_PERFORMANCE_ANALYSIS_EXECUTABLE_FIX_343 is True

    def test_fix_343_optimization_not_truth_reduction(self) -> None:
        board = build_intelligence_performance_evidence_scalability_program(
            session_id=SESSION
        ).intelligence_performance_evidence_scalability_program
        assert set(board["fix_343_certification_requirements"]) == set(FIX_343_CERTIFICATION_REQUIREMENTS)
        assert board["truth_reduction"] is False
        assert "truth_reduction" in INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_INVARIANT

    def test_fix_343_phases_present(self) -> None:
        sections = build_intelligence_performance_evidence_scalability_program(
            session_id=SESSION
        ).intelligence_performance_evidence_scalability_program["sections"]
        for phase in INTELLIGENCE_PERFORMANCE_PHASES:
            assert sections[phase]

    def test_fix_343_certification_requirement_count(self) -> None:
        assert len(FIX_343_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_343_route_id(self) -> None:
        assert INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ROUTE_ID == (
            "workstream_intelligence_performance_evidence_scalability_program"
        )
