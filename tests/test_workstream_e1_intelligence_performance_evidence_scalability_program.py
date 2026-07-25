# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E1 — intelligence performance & evidence scalability tests."""

from __future__ import annotations

import pytest

from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_contract import (
    AUTHORITY_EXPANSION_FIX_343,
    BASELINE_COMPOSE_TIMINGS_SEC,
    INTELLIGENCE_PERFORMANCE_PHASES,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ID,
    TRUTH_REDUCTION_FIX_343,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_executor import (
    build_compose_dependency_report,
    build_compose_hotspot_registry,
    run_intelligence_performance_analysis,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_intent import (
    handle_intelligence_performance_evidence_scalability_intent,
    parse_intelligence_performance_evidence_scalability_intent,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_renderer import (
    render_all_intelligence_performance_deliverables,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_service import (
    build_intelligence_performance_evidence_scalability_program,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_store import (
    clear_intelligence_performance_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_intelligence_performance_records_for_tests()
    yield
    clear_intelligence_performance_records_for_tests()


def test_workstream_phases():
    assert INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ID == "WORKSTREAM_E1"
    assert len(INTELLIGENCE_PERFORMANCE_PHASES) == 9
    assert BASELINE_COMPOSE_TIMINGS_SEC["FIX 322"] > BASELINE_COMPOSE_TIMINGS_SEC["FIX 323"]


def test_intent_parsing():
    assert parse_intelligence_performance_evidence_scalability_intent(
        "show intelligence performance dashboard"
    ) == {"action": "view", "focus": "intelligence_performance_dashboard"}
    assert parse_intelligence_performance_evidence_scalability_intent("analyze intelligence performance") == {
        "action": "analyze"
    }
    review = parse_intelligence_performance_evidence_scalability_intent(
        "performance review approve: Human approves intelligence performance optimization plan"
    )
    assert review["kind"] == "performance_review_approve"


def test_program_phases_and_outputs():
    board = build_intelligence_performance_evidence_scalability_program(
        session_id="ws-e1-empty"
    ).intelligence_performance_evidence_scalability_program
    assert board["workstream_id"] == INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ID
    assert board["truth_reduction"] is False
    assert board["authority_expansion"] is False
    for phase in INTELLIGENCE_PERFORMANCE_PHASES:
        assert phase in board["sections"]


def test_dependency_and_hotspot_analysis():
    session_id = "ws-e1-analysis"
    run_intelligence_performance_analysis(session_id=session_id)
    deps = build_compose_dependency_report(session_id=session_id)
    assert deps["duplicate_compose_paths"]
    assert deps["recursive_fan_in_chains"]
    hotspots = build_compose_hotspot_registry(session_id=session_id)
    assert hotspots["slowest_module"] == "FIX 322"
    assert hotspots["hotspot_count"] >= 2

    handle_intelligence_performance_evidence_scalability_intent(
        parse_intelligence_performance_evidence_scalability_intent(
            "performance review approve: Human approves intelligence performance optimization plan"
        ),
        session_id=session_id,
    )
    board = build_intelligence_performance_evidence_scalability_program(
        session_id=session_id
    ).intelligence_performance_evidence_scalability_program
    assert board["success_criteria"]["program_complete"] is True
    assert board["latency_trends"]["scalability_risk"] is True


def test_deliverable_renderers():
    run_intelligence_performance_analysis(session_id="ws-e1-render")
    board = build_intelligence_performance_evidence_scalability_program(
        session_id="ws-e1-render"
    ).intelligence_performance_evidence_scalability_program
    deliverables = render_all_intelligence_performance_deliverables(board)
    assert set(deliverables) == {
        "INTELLIGENCE_PERFORMANCE_REPORT.md",
        "COMPOSE_DEPENDENCY_ANALYSIS.md",
        "EVIDENCE_SCALABILITY_REPORT.md",
    }
    assert "Performance optimization ≠ truth reduction" in deliverables["INTELLIGENCE_PERFORMANCE_REPORT.md"]
    assert TRUTH_REDUCTION_FIX_343 is False
    assert AUTHORITY_EXPANSION_FIX_343 is False
