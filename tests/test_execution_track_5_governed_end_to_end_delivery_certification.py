# SPDX-License-Identifier: Apache-2.0
"""EXECUTION_TRACK_5 — end-to-end delivery certification tests."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store import (
    clear_governed_deployment_execution_records_for_tests,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_contract import (
    CERTIFICATION_SCENARIO_IDS,
    DELIVERY_AUTHORITY_FIX_338,
    EXECUTION_TRACK_5_ID,
    EXECUTION_TRACK_5_PHASES,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_executor import (
    assess_certification_status,
    run_certification_scenario,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_intent import (
    handle_governed_end_to_end_delivery_certification_intent,
    parse_governed_end_to_end_delivery_certification_intent,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_renderer import (
    render_all_governed_end_to_end_delivery_certification_deliverables,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_service import (
    build_governed_end_to_end_delivery_certification,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store import (
    clear_governed_end_to_end_delivery_certification_records_for_tests,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    clear_governed_git_delivery_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()


def _seed_certification_reviews(session_id: str) -> None:
    for text in (
        "certification review: scenario=fastapi_railway provider=railway",
        "certification readiness review: All ET1-ET4 tracks ready for certification",
        "certification evidence review: Evidence bundle reviewed for certification",
    ):
        intent = parse_governed_end_to_end_delivery_certification_intent(text)
        assert intent is not None
        handle_governed_end_to_end_delivery_certification_intent(intent, session_id=session_id)


def _run_core_scenarios(session_id: str) -> None:
    for scenario_id in (
        "scenario_1_fastapi_railway",
        "scenario_2_spring_boot_railway",
        "scenario_3_nextjs_vercel",
    ):
        result = run_certification_scenario(session_id=session_id, scenario_id=scenario_id)
        assert result["passed"] is True, result


def test_execution_track_phases():
    assert EXECUTION_TRACK_5_ID == "EXECUTION_TRACK_5"
    assert len(EXECUTION_TRACK_5_PHASES) == 9
    assert len(CERTIFICATION_SCENARIO_IDS) == 5


def test_intent_parsing():
    assert parse_governed_end_to_end_delivery_certification_intent(
        "show delivery certification dashboard"
    ) == {"action": "view", "focus": "delivery_certification_dashboard"}
    parsed = parse_governed_end_to_end_delivery_certification_intent(
        "certification decision approve: Human approves end-to-end delivery certification"
    )
    assert parsed == {
        "action": "record",
        "kind": "certification_decision_approve",
        "content": "Human approves end-to-end delivery certification",
    }
    run_intent = parse_governed_end_to_end_delivery_certification_intent(
        "certification run: scenario=fastapi_railway"
    )
    assert run_intent == {
        "action": "run",
        "scenario_id": "scenario_1_fastapi_railway",
        "metadata": {"scenario": "fastapi_railway"},
    }


def test_program_phases_and_outputs():
    result = build_governed_end_to_end_delivery_certification(session_id="et5-empty")
    board = result.governed_end_to_end_delivery_certification
    assert board["execution_track_id"] == EXECUTION_TRACK_5_ID
    assert board["delivery_authority"] is False
    assert board["automatic_certification_promotion"] is False
    for phase in EXECUTION_TRACK_5_PHASES:
        assert phase in board["sections"]


def test_certification_run_and_status():
    session_id = "et5-cert"
    _seed_certification_reviews(session_id)
    _run_core_scenarios(session_id)

    status_before = assess_certification_status(session_id=session_id)
    assert status_before["status"] == "PARTIALLY_CERTIFIED"
    assert status_before["all_core_scenarios_passed"] is True

    intent = parse_governed_end_to_end_delivery_certification_intent(
        "certification decision approve: Human approves governed delivery certification"
    )
    assert intent is not None
    handle_governed_end_to_end_delivery_certification_intent(intent, session_id=session_id)

    status_after = assess_certification_status(session_id=session_id)
    assert status_after["status"] == "CERTIFIED"
    assert status_after["delivery_authority_granted"] is False


def test_documentation_scenario_skips_deployment():
    result = run_certification_scenario(
        session_id="et5-docs",
        scenario_id="scenario_5_documentation_change",
    )
    assert result["passed"] is True
    deployment = result["run"]["stage_results"]["deployment"]
    assert deployment.get("skipped") is True


def test_deliverable_renderers():
    session_id = "et5-render"
    _seed_certification_reviews(session_id)
    _run_core_scenarios(session_id)
    handle_governed_end_to_end_delivery_certification_intent(
        parse_governed_end_to_end_delivery_certification_intent(
            "certification decision approve: Human approves certification for render test"
        ),
        session_id=session_id,
    )
    result = build_governed_end_to_end_delivery_certification(session_id=session_id)
    deliverables = render_all_governed_end_to_end_delivery_certification_deliverables(
        result.governed_end_to_end_delivery_certification
    )
    assert set(deliverables) == {
        "END_TO_END_DELIVERY_CERTIFICATION_REPORT.md",
        "DELIVERY_RELIABILITY_REPORT.md",
        "DELIVERY_CERTIFICATION_EVIDENCE_REPORT.md",
    }
    assert "Delivery certification ≠ delivery authority" in deliverables[
        "END_TO_END_DELIVERY_CERTIFICATION_REPORT.md"
    ]
    assert DELIVERY_AUTHORITY_FIX_338 is False
