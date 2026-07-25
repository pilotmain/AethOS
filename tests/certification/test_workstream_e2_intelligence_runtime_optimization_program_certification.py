# SPDX-License-Identifier: Apache-2.0
"""FIX 344 / WORKSTREAM_E2 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_344_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_contract import (
    AUTHORITY_EXPANSION_FIX_344,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_344,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PHASES,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_FIX,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ID,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_INVARIANT,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ROUTE_ID,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_SCHEMA_VERSION,
    LOCAL_RUNTIME_OPTIMIZATION_EXECUTABLE_FIX_344,
    TRUST_MUTATION_AUTHORITY_FIX_344,
    TRUTH_REDUCTION_FIX_344,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_service import (
    build_intelligence_runtime_optimization_program,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_store import (
    clear_intelligence_runtime_optimization_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-e2-cert-344"


@pytest.fixture(autouse=True)
def _clean():
    clear_intelligence_runtime_optimization_records_for_tests()
    yield
    clear_intelligence_runtime_optimization_records_for_tests()


class TestWorkstreamE2IntelligenceRuntimeOptimizationCertification:
    def test_fix_344_contract(self) -> None:
        assert INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_FIX == "FIX 344"
        assert INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ID == "WORKSTREAM_E2"
        assert INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_SCHEMA_VERSION == (
            "workstream_intelligence_runtime_optimization_program_v1"
        )
        assert TRUTH_REDUCTION_FIX_344 is False
        assert AUTHORITY_EXPANSION_FIX_344 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_344 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_344 is False
        assert LOCAL_RUNTIME_OPTIMIZATION_EXECUTABLE_FIX_344 is True

    def test_fix_344_optimization_not_truth_reduction(self) -> None:
        board = build_intelligence_runtime_optimization_program(
            session_id=SESSION
        ).intelligence_runtime_optimization_program
        assert set(board["fix_344_certification_requirements"]) == set(FIX_344_CERTIFICATION_REQUIREMENTS)
        assert board["truth_reduction"] is False
        assert "truth_reduction" in INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_INVARIANT

    def test_fix_344_phases_present(self) -> None:
        sections = build_intelligence_runtime_optimization_program(
            session_id=SESSION
        ).intelligence_runtime_optimization_program["sections"]
        for phase in INTELLIGENCE_RUNTIME_OPTIMIZATION_PHASES:
            assert sections[phase]

    def test_fix_344_certification_requirement_count(self) -> None:
        assert len(FIX_344_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_344_route_id(self) -> None:
        assert INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ROUTE_ID == (
            "workstream_intelligence_runtime_optimization_program"
        )
