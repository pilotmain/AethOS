# SPDX-License-Identifier: Apache-2.0
"""FIX 340 / WORKSTREAM_C2 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_340_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_contract import (
    AUTONOMOUS_MUTATION_ENABLED_FIX_340,
    AUTHORITY_EXPANSION_FIX_340,
    DELIVERY_AUTHORITY_FIX_340,
    DELIVERY_OPTIMIZATION_PHASES,
    DELIVERY_OPTIMIZATION_PROGRAM_FIX,
    DELIVERY_OPTIMIZATION_PROGRAM_ID,
    DELIVERY_OPTIMIZATION_PROGRAM_INVARIANT,
    DELIVERY_OPTIMIZATION_PROGRAM_ROUTE_ID,
    DELIVERY_OPTIMIZATION_PROGRAM_SCHEMA_VERSION,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_340,
    LOCAL_OPTIMIZATION_ANALYSIS_EXECUTABLE_FIX_340,
    TRUST_MUTATION_AUTHORITY_FIX_340,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_service import (
    build_delivery_optimization_program,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_store import (
    clear_delivery_optimization_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-c2-cert-340"


@pytest.fixture(autouse=True)
def _clean():
    clear_delivery_optimization_records_for_tests()
    yield
    clear_delivery_optimization_records_for_tests()


class TestWorkstreamC2DeliveryOptimizationProgramCertification:
    def test_fix_340_contract(self) -> None:
        assert DELIVERY_OPTIMIZATION_PROGRAM_FIX == "FIX 340"
        assert DELIVERY_OPTIMIZATION_PROGRAM_ID == "WORKSTREAM_C2"
        assert DELIVERY_OPTIMIZATION_PROGRAM_SCHEMA_VERSION == "workstream_delivery_optimization_program_v1"
        assert AUTONOMOUS_MUTATION_ENABLED_FIX_340 is False
        assert DELIVERY_AUTHORITY_FIX_340 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_340 is False
        assert AUTHORITY_EXPANSION_FIX_340 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_340 is False
        assert LOCAL_OPTIMIZATION_ANALYSIS_EXECUTABLE_FIX_340 is True

    def test_fix_340_optimization_not_autonomous_mutation(self) -> None:
        board = build_delivery_optimization_program(session_id=SESSION).delivery_optimization_program
        assert set(board["fix_340_certification_requirements"]) == set(FIX_340_CERTIFICATION_REQUIREMENTS)
        assert board["autonomous_mutation_enabled"] is False
        assert "mutation" in DELIVERY_OPTIMIZATION_PROGRAM_INVARIANT

    def test_fix_340_phases_present(self) -> None:
        sections = build_delivery_optimization_program(session_id=SESSION).delivery_optimization_program["sections"]
        for phase in DELIVERY_OPTIMIZATION_PHASES:
            assert sections[phase]

    def test_fix_340_certification_requirement_count(self) -> None:
        assert len(FIX_340_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_340_route_id(self) -> None:
        assert DELIVERY_OPTIMIZATION_PROGRAM_ROUTE_ID == "workstream_delivery_optimization_program"
