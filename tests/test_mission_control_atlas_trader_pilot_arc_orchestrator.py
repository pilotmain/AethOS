# SPDX-License-Identifier: Apache-2.0
"""FIX 193 — Atlas Trader pilot arc orchestrator tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
    ATLAS_PILOT_SESSIONS,
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_ROUTE_ID,
    TRUST_GRANTING_AUTHORITY_FIX_193,
    TRUST_INHERITANCE_ENABLED_FIX_193,
)
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_intent import (
    is_atlas_trader_pilot_arc_orchestrator_intent,
    parse_atlas_trader_pilot_arc_orchestrator_record_intent,
)
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_service import (
    build_atlas_trader_pilot_arc_orchestrator,
    run_atlas_trader_pilot_arc_pilot,
)
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_store import (
    append_atlas_trader_pilot_arc_orchestrator_record,
    clear_atlas_trader_pilot_arc_orchestrator_records_for_tests,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    persist_pilot_run_audit,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    PHASE_2_REPOSITORY_ORDER,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
    append_independent_repository_trust_expansion_record,
    clear_independent_repository_trust_expansion_records_for_tests,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
    append_pilotos_ui_trust_report_freeze_record,
    clear_pilotos_ui_trust_report_freeze_records_for_tests,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
    RepoPilotReadinessDashboardResult,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_atlas_trader_pilot_arc_orchestrator_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_pilotos_ui_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_atlas_trader_pilot_arc_orchestrator_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_pilotos_ui_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()


def _seed_atlas_expansion_approval() -> None:
    append_independent_repository_trust_expansion_record(
        session_id="fix-193-test",
        kind="repo_expansion_approval",
        content="Operator approves pilotmain/atlas-trader for independent pilot arc",
        repository=PHASE_2_REPOSITORY_ORDER[1],
    )


def _seed_pilotos_trust_baseline() -> None:
    append_pilotos_ui_trust_report_freeze_record(
        session_id="fix-193-test",
        kind="human_trust_decision_approve",
        content="PilotOS UI trust baseline satisfied for Atlas expansion",
    )


def _seed_atlas_pilot_audits() -> None:
    persist_pilot_run_audit(
        {
            "session_id": ATLAS_PILOT_SESSIONS[0],
            "repo_issue": "pilotmain/atlas-trader#1",
            "outcome": "complete",
            "stages_completed": ["issue_intake"],
            "pilot_report": {"stages_satisfied": ["issue_intake", "implementation_plan"]},
            "blockers": [],
        }
    )
    persist_pilot_run_audit(
        {
            "session_id": ATLAS_PILOT_SESSIONS[1],
            "repo_issue": "pilotmain/atlas-trader#1",
            "outcome": "partial",
            "blockers": ["stage_blocked:intent_alignment"],
            "pilot_report": {"stages_pending": ["intent_alignment"]},
        }
    )
    persist_pilot_run_audit(
        {
            "session_id": ATLAS_PILOT_SESSIONS[2],
            "repo_issue": "pilotmain/atlas-trader#1",
            "outcome": "complete",
            "stages_completed": ["pr_open"],
            "pilot_report": {
                "stages_satisfied": [
                    "issue_intake",
                    "implementation_plan",
                    "patch_proposal",
                    "pr_open",
                ],
            },
            "blockers": [],
        }
    )


def _atlas_arc_stack() -> None:
    _seed_atlas_expansion_approval()
    _seed_pilotos_trust_baseline()
    _seed_atlas_pilot_audits()


def test_atlas_pilot_arc_intent():
    assert is_atlas_trader_pilot_arc_orchestrator_intent("show atlas pilot arc")
    assert is_atlas_trader_pilot_arc_orchestrator_intent("atlas pilot dashboard")
    assert not is_atlas_trader_pilot_arc_orchestrator_intent("auto trust atlas")


def test_atlas_pilot_arc_record_intent():
    parsed = parse_atlas_trader_pilot_arc_orchestrator_record_intent(
        "atlas pilot arc issue: pilotmain/atlas-trader#1"
    )
    assert parsed == ("repo_issue_binding", "pilotmain/atlas-trader#1")

    obs = parse_atlas_trader_pilot_arc_orchestrator_record_intent(
        "atlas pilot observation: alignment drift on intake"
    )
    assert obs == ("atlas_pilot_observation", "alignment drift on intake")


def test_build_atlas_pilot_arc_unproven_without_gates():
    result = build_atlas_trader_pilot_arc_orchestrator(session_id="fix-193-test")
    assert result.ok is True
    report = result.atlas_trader_pilot_arc_orchestrator
    assert report["arc_state"] == "UNPROVEN"
    assert report["trust_granting_authority"] is TRUST_GRANTING_AUTHORITY_FIX_193
    assert report["trust_inheritance_enabled"] is TRUST_INHERITANCE_ENABLED_FIX_193
    assert "fix_187_expansion_not_approved" in result.blockers


@patch(
    "aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator."
    "atlas_trader_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
)
def test_atlas_pilot_arc_state_trust_review_pending_without_auto_trust(mock_readiness):
    mock_readiness.return_value = RepoPilotReadinessDashboardResult(
        ok=True,
        session_id="default",
        blockers=[],
    )
    _atlas_arc_stack()
    result = build_atlas_trader_pilot_arc_orchestrator(session_id="fix-193-test")
    report = result.atlas_trader_pilot_arc_orchestrator
    assert report["arc_state"] == "TRUST_REVIEW_PENDING"
    rec = report["sections"]["atlas_trust_recommendation"][0]
    assert rec["trust_status"] == "TRUST_REVIEW_PENDING"
    assert rec["trust_granted_automatically"] is False


@patch(
    "aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator."
    "atlas_trader_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
)
def test_operator_trust_decision_required_for_conditionally_trusted(mock_readiness):
    mock_readiness.return_value = RepoPilotReadinessDashboardResult(
        ok=True,
        session_id="default",
        blockers=[],
    )
    _atlas_arc_stack()
    record, blockers = append_atlas_trader_pilot_arc_orchestrator_record(
        session_id="fix-193-test",
        kind="pilot_arc_trust_decision",
        content="CONDITIONALLY_TRUSTED — operator review complete",
        metadata={"trust_status": "CONDITIONALLY_TRUSTED"},
    )
    assert not blockers
    assert record
    result = build_atlas_trader_pilot_arc_orchestrator(session_id="fix-193-test")
    assert result.atlas_trader_pilot_arc_orchestrator["arc_state"] == "CONDITIONALLY_TRUSTED"


def test_run_atlas_pilot_blocked_without_gates():
    outcome = run_atlas_trader_pilot_arc_pilot(pilot_number=1)
    assert outcome.ok is False
    assert "fix_187_expansion_not_approved" in outcome.blockers


@patch(
    "aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator."
    "atlas_trader_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
)
def test_run_atlas_pilot_routes_through_fix_181(mock_readiness):
    mock_readiness.return_value = RepoPilotReadinessDashboardResult(
        ok=True,
        session_id="default",
        blockers=[],
    )
    _seed_atlas_expansion_approval()
    _seed_pilotos_trust_baseline()
    with patch(
        "aethos_core.mission_control.end_to_end_repo_development_pilot_harness."
        "end_to_end_repo_development_pilot_harness_service.run_end_to_end_repo_development_pilot",
        return_value=type(
            "Outcome",
            (),
            {
                "ok": True,
                "audit_id": "atlas-audit-1",
                "stages_completed": ["issue_intake"],
                "blockers": [],
            },
        )(),
    ):
        outcome = run_atlas_trader_pilot_arc_pilot(pilot_number=1)
    assert outcome.ok is True
    assert outcome.session_id == ATLAS_PILOT_SESSIONS[0]
    assert outcome.audit_id == "atlas-audit-1"


@patch(
    "aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator."
    "atlas_trader_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
)
def test_chat_route_show_atlas_pilot_arc(mock_readiness):
    mock_readiness.return_value = RepoPilotReadinessDashboardResult(
        ok=True,
        session_id="default",
        blockers=[],
    )
    _atlas_arc_stack()
    turn = resolve_chat_turn("show atlas pilot arc", session_id="fix-193-chat")
    assert turn.intent == "mission_control_atlas_trader_pilot_arc_orchestrator"
    assert (turn.meta or {}).get("route_id") == ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_ROUTE_ID


@patch(
    "aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator."
    "atlas_trader_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
)
def test_atlas_pilot_arc_api(mock_readiness):
    mock_readiness.return_value = RepoPilotReadinessDashboardResult(
        ok=True,
        session_id="default",
        blockers=[],
    )
    _atlas_arc_stack()
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/atlas-trader-pilot-arc-orchestrator",
        params={"session_id": "fix-193-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["trust_granting_authority"] is False
    assert payload["atlas_trader_pilot_arc_orchestrator"]["arc_state"] == "TRUST_REVIEW_PENDING"
