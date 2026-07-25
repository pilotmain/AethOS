# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E2 — intelligence runtime optimization tests."""

from __future__ import annotations

import pytest

from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_compose_cache import (
    clear_intelligence_runtime_compose_cache_for_tests,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_contract import (
    AUTHORITY_EXPANSION_FIX_344,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PHASES,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ID,
    RUNTIME_BASELINE_COMPOSE_TIMINGS_SEC,
    TRUTH_REDUCTION_FIX_344,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_executor import (
    build_dependency_flattening_report,
    build_runtime_hotspot_registry,
    run_runtime_optimization_analysis,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_intent import (
    handle_intelligence_runtime_optimization_intent,
    parse_intelligence_runtime_optimization_intent,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_renderer import (
    render_all_intelligence_runtime_optimization_deliverables,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_service import (
    build_intelligence_runtime_optimization_program,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_store import (
    clear_intelligence_runtime_optimization_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_intelligence_runtime_optimization_records_for_tests()
    clear_intelligence_runtime_compose_cache_for_tests()
    yield
    clear_intelligence_runtime_optimization_records_for_tests()
    clear_intelligence_runtime_compose_cache_for_tests()


def test_workstream_phases():
    assert INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ID == "WORKSTREAM_E2"
    assert len(INTELLIGENCE_RUNTIME_OPTIMIZATION_PHASES) == 9
    assert RUNTIME_BASELINE_COMPOSE_TIMINGS_SEC["FIX 322"] > RUNTIME_BASELINE_COMPOSE_TIMINGS_SEC["FIX 323"]


def test_intent_parsing():
    assert parse_intelligence_runtime_optimization_intent("show runtime optimization dashboard") == {
        "action": "view",
        "focus": "runtime_optimization_dashboard",
    }
    assert parse_intelligence_runtime_optimization_intent("analyze runtime optimization") == {"action": "analyze"}
    review = parse_intelligence_runtime_optimization_intent(
        "runtime optimization review approve: Human approves runtime optimization priority matrix"
    )
    assert review["kind"] == "runtime_optimization_review_approve"


def test_program_phases_and_outputs():
    board = build_intelligence_runtime_optimization_program(
        session_id="ws-e2-empty"
    ).intelligence_runtime_optimization_program
    assert board["workstream_id"] == INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ID
    assert board["truth_reduction"] is False
    assert board["authority_expansion"] is False
    for phase in INTELLIGENCE_RUNTIME_OPTIMIZATION_PHASES:
        assert phase in board["sections"]


def test_runtime_analysis_and_flattening():
    session_id = "ws-e2-analysis"
    analysis = run_runtime_optimization_analysis(session_id=session_id)
    flattening = build_dependency_flattening_report(session_id=session_id)
    assert flattening["current_chain"][0] == "FIX 323"
    assert flattening["target_chain"][-1] == "FIX 322 Snapshot"
    assert flattening["dependency_depth_reduction"] >= 1
    assert analysis["runtime_metrics"]["compose_duration_reduction"] > 0
    assert analysis["probe"]["artifact_snapshot_used"] is True

    hotspots = build_runtime_hotspot_registry(session_id=session_id)
    assert hotspots["slowest_module"] == "FIX 322"

    handle_intelligence_runtime_optimization_intent(
        parse_intelligence_runtime_optimization_intent(
            "runtime optimization review approve: Human approves runtime optimization priority matrix"
        ),
        session_id=session_id,
    )
    board = build_intelligence_runtime_optimization_program(
        session_id=session_id
    ).intelligence_runtime_optimization_program
    assert board["success_criteria"]["program_complete"] is True


def test_deliverable_renderers():
    run_runtime_optimization_analysis(session_id="ws-e2-render")
    board = build_intelligence_runtime_optimization_program(
        session_id="ws-e2-render"
    ).intelligence_runtime_optimization_program
    deliverables = render_all_intelligence_runtime_optimization_deliverables(board)
    assert set(deliverables) == {
        "INTELLIGENCE_RUNTIME_OPTIMIZATION_REPORT.md",
        "DEPENDENCY_FLATTENING_ANALYSIS.md",
        "RUNTIME_SCALABILITY_REPORT.md",
    }
    assert "Runtime optimization ≠ truth reduction" in deliverables["INTELLIGENCE_RUNTIME_OPTIMIZATION_REPORT.md"]
    assert TRUTH_REDUCTION_FIX_344 is False
    assert AUTHORITY_EXPANSION_FIX_344 is False
