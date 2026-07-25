# SPDX-License-Identifier: Apache-2.0
"""FIX 346 / WORKSTREAM_E4 certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_346_CERTIFICATION_REQUIREMENTS
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_contract import (
    AUTHORITY_EXPANSION_FIX_346,
    COMPOSE_RUNTIME_GUARDRAILS_PHASES,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_FIX,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ID,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_INVARIANT,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ROUTE_ID,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_SCHEMA_VERSION,
    EVIDENCE_REDUCTION_FIX_346,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_346,
    LOCAL_RUNTIME_GUARDRAIL_EXECUTABLE_FIX_346,
    TRUST_MUTATION_AUTHORITY_FIX_346,
    TRUTH_MUTATION_FIX_346,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_service import (
    build_compose_runtime_guardrails_program,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_store import (
    clear_compose_runtime_guardrails_records_for_tests,
)

pytestmark = pytest.mark.certification

SESSION = "ws-e4-cert-346"


@pytest.fixture(autouse=True)
def _clean():
    clear_compose_runtime_guardrails_records_for_tests()
    yield
    clear_compose_runtime_guardrails_records_for_tests()


class TestWorkstreamE4ComposeRuntimeGuardrailsCertification:
    def test_fix_346_contract(self) -> None:
        assert COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_FIX == "FIX 346"
        assert COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ID == "WORKSTREAM_E4"
        assert COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_SCHEMA_VERSION == (
            "workstream_compose_runtime_guardrails_program_v1"
        )
        assert TRUTH_MUTATION_FIX_346 is False
        assert EVIDENCE_REDUCTION_FIX_346 is False
        assert AUTHORITY_EXPANSION_FIX_346 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_346 is False
        assert GOVERNANCE_BYPASS_AUTHORITY_FIX_346 is False
        assert LOCAL_RUNTIME_GUARDRAIL_EXECUTABLE_FIX_346 is True

    def test_fix_346_guardrails_not_evidence_reduction(self) -> None:
        board = build_compose_runtime_guardrails_program(
            session_id=SESSION
        ).compose_runtime_guardrails_program
        assert set(board["fix_346_certification_requirements"]) == set(FIX_346_CERTIFICATION_REQUIREMENTS)
        assert board["evidence_reduction"] is False
        assert "evidence_reduction" in COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_INVARIANT

    def test_fix_346_phases_present(self) -> None:
        sections = build_compose_runtime_guardrails_program(
            session_id=SESSION
        ).compose_runtime_guardrails_program["sections"]
        for phase in COMPOSE_RUNTIME_GUARDRAILS_PHASES:
            assert sections[phase]

    def test_fix_346_certification_requirement_count(self) -> None:
        assert len(FIX_346_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_346_route_id(self) -> None:
        assert COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ROUTE_ID == "workstream_compose_runtime_guardrails_program"
