# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E3 — intelligence scalability implementation tests."""

from __future__ import annotations

import pytest

from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_compose_cache import (
    clear_intelligence_runtime_compose_cache_for_tests,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalable_compose_bridge import (
    clear_scalable_compose_sessions_for_tests,
    disable_scalable_compose,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_contract import (
    AUTHORITY_EXPANSION_FIX_345,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PHASES,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ID,
    TRUTH_MUTATION_FIX_345,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_executor import (
    execute_scalability_implementation,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_intent import (
    handle_intelligence_scalability_implementation_intent,
    parse_intelligence_scalability_implementation_intent,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_renderer import (
    render_all_intelligence_scalability_implementation_deliverables,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_service import (
    build_intelligence_scalability_implementation_program,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_store import (
    clear_intelligence_scalability_implementation_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_intelligence_scalability_implementation_records_for_tests()
    clear_intelligence_runtime_compose_cache_for_tests()
    clear_scalable_compose_sessions_for_tests()
    yield
    clear_intelligence_scalability_implementation_records_for_tests()
    clear_intelligence_runtime_compose_cache_for_tests()
    clear_scalable_compose_sessions_for_tests()


def test_workstream_phases():
    assert INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ID == "WORKSTREAM_E3"
    assert len(INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PHASES) == 9


def test_intent_parsing():
    assert parse_intelligence_scalability_implementation_intent("show intelligence scalability dashboard") == {
        "action": "view",
        "focus": "intelligence_scalability_dashboard",
    }
    assert parse_intelligence_scalability_implementation_intent("execute scalability implementation") == {
        "action": "execute"
    }
    review = parse_intelligence_scalability_implementation_intent(
        "scalability review approve: Human approves scalability implementation"
    )
    assert review["kind"] == "scalability_review_approve"


def test_program_phases_and_outputs():
    board = build_intelligence_scalability_implementation_program(
        session_id="ws-e3-empty"
    ).intelligence_scalability_implementation_program
    assert board["workstream_id"] == INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ID
    assert board["truth_mutation"] is False
    assert board["authority_expansion"] is False
    for phase in INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PHASES:
        assert phase in board["sections"]


def test_scalability_implementation_execution():
    session_id = "ws-e3-exec"
    result = execute_scalability_implementation(session_id=session_id, lightweight=True)
    assert result["ok"] is True
    assert result["dependency_flattening_execution_report"]["flattened"] is True
    assert result["truth_preservation_report"]["truth_mutation_performed"] is False
    assert result["runtime_benchmark_report"]["compose_duration_reduction_pct"] > 0

    handle_intelligence_scalability_implementation_intent(
        parse_intelligence_scalability_implementation_intent(
            "scalability review approve: Human approves scalability implementation"
        ),
        session_id=session_id,
    )
    board = build_intelligence_scalability_implementation_program(
        session_id=session_id
    ).intelligence_scalability_implementation_program
    assert board["success_criteria"]["program_complete"] is True

    deliverables = render_all_intelligence_scalability_implementation_deliverables(board)
    assert set(deliverables) == {
        "INTELLIGENCE_SCALABILITY_IMPLEMENTATION_REPORT.md",
        "RUNTIME_BENCHMARK_REPORT.md",
        "TRUTH_PRESERVATION_REPORT.md",
    }
    assert "Optimization execution ≠ truth mutation" in deliverables["INTELLIGENCE_SCALABILITY_IMPLEMENTATION_REPORT.md"]
    assert TRUTH_MUTATION_FIX_345 is False
    assert AUTHORITY_EXPANSION_FIX_345 is False
    disable_scalable_compose(session_id=session_id)
