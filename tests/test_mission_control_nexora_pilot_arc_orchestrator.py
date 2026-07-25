# SPDX-License-Identifier: Apache-2.0
"""FIX 195 — Nexora pilot arc orchestrator tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_store import (
    append_atlas_trader_trust_report_freeze_record,
    clear_atlas_trader_trust_report_freeze_records_for_tests,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
    build_cross_repository_multi_agent_delivery_validation,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
    append_dogfood_pilot_trust_report_freeze_record,
    clear_dogfood_pilot_trust_report_freeze_records_for_tests,
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
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_contract import (
    NEXORA_PILOT_ARC_ORCHESTRATOR_ROUTE_ID,
    NEXORA_PILOT_SESSIONS,
    NEXORA_REPOSITORY,
    TRUST_GRANTING_AUTHORITY_FIX_195,
    TRUST_INHERITANCE_ENABLED_FIX_195,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_intent import (
    is_nexora_pilot_arc_orchestrator_intent,
    parse_nexora_pilot_arc_orchestrator_record_intent,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_service import (
    build_nexora_pilot_arc_orchestrator,
    run_nexora_pilot_arc_pilot,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_store import (
    clear_nexora_pilot_arc_orchestrator_records_for_tests,
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
    clear_nexora_pilot_arc_orchestrator_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_dogfood_pilot_trust_report_freeze_records_for_tests()
    clear_pilotos_ui_trust_report_freeze_records_for_tests()
    clear_atlas_trader_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_nexora_pilot_arc_orchestrator_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_dogfood_pilot_trust_report_freeze_records_for_tests()
    clear_pilotos_ui_trust_report_freeze_records_for_tests()
    clear_atlas_trader_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()


def _seed_nexora_expansion_approval() -> None:
    append_independent_repository_trust_expansion_record(
        session_id="fix-195-test",
        kind="repo_expansion_approval",
        content="Operator approves pilotmain/nexora-monorepo-starter for independent pilot arc",
        repository=PHASE_2_REPOSITORY_ORDER[2],
    )


def _seed_upstream_trust_baselines() -> None:
    append_dogfood_pilot_trust_report_freeze_record(
        session_id="fix-195-test",
        kind="trust_report_freeze_artifact",
        content="AethOS trust baseline frozen",
    )
    append_pilotos_ui_trust_report_freeze_record(
        session_id="fix-195-test",
        kind="human_trust_decision_approve",
        content="PilotOS UI trust baseline satisfied",
    )
    append_atlas_trader_trust_report_freeze_record(
        session_id="fix-195-test",
        kind="human_trust_decision_approve",
        content="Atlas Trader trust baseline satisfied",
    )


def _seed_nexora_pilot_audits() -> None:
    persist_pilot_run_audit(
        {
            "session_id": NEXORA_PILOT_SESSIONS[0],
            "repo_issue": "pilotmain/nexora-monorepo-starter#1",
            "outcome": "complete",
            "stages_completed": ["issue_intake"],
            "pilot_report": {"stages_satisfied": ["issue_intake", "implementation_plan"]},
            "blockers": [],
        }
    )
    persist_pilot_run_audit(
        {
            "session_id": NEXORA_PILOT_SESSIONS[1],
            "repo_issue": "pilotmain/nexora-monorepo-starter#1",
            "outcome": "partial",
            "blockers": ["stage_blocked:intent_alignment"],
            "pilot_report": {"stages_pending": ["intent_alignment"]},
        }
    )
    persist_pilot_run_audit(
        {
            "session_id": NEXORA_PILOT_SESSIONS[2],
            "repo_issue": "pilotmain/nexora-monorepo-starter#1",
            "outcome": "complete",
            "stages_completed": ["pr_open"],
            "pilot_report": {
                "stages_satisfied": ["issue_intake", "implementation_plan", "patch_proposal", "pr_open"],
            },
            "blockers": [],
        }
    )


def _nexora_arc_stack() -> None:
    _seed_nexora_expansion_approval()
    _seed_upstream_trust_baselines()
    _seed_nexora_pilot_audits()


def test_nexora_pilot_arc_intent():
    assert is_nexora_pilot_arc_orchestrator_intent("show nexora pilot arc")
    assert is_nexora_pilot_arc_orchestrator_intent("nexora pilot dashboard")
    assert not is_nexora_pilot_arc_orchestrator_intent("auto trust nexora")


def test_nexora_pilot_arc_record_intent():
    parsed = parse_nexora_pilot_arc_orchestrator_record_intent(
        "nexora pilot arc issue: pilotmain/nexora-monorepo-starter#1"
    )
    assert parsed == ("repo_issue_binding", "pilotmain/nexora-monorepo-starter#1")

    obs = parse_nexora_pilot_arc_orchestrator_record_intent(
        "nexora pilot observation: scope fidelity check on intake"
    )
    assert obs == ("nexora_pilot_observation", "scope fidelity check on intake")


def test_build_nexora_pilot_arc_unproven_without_gates():
    result = build_nexora_pilot_arc_orchestrator(session_id="fix-195-test")
    assert result.ok is True
    report = result.nexora_pilot_arc_orchestrator
    assert report["arc_state"] == "UNPROVEN"
    assert report["trust_granting_authority"] is TRUST_GRANTING_AUTHORITY_FIX_195
    assert report["trust_inheritance_enabled"] is TRUST_INHERITANCE_ENABLED_FIX_195
    assert "fix_187_expansion_not_approved" in result.blockers


@patch(
    "aethos_core.mission_control.nexora_pilot_arc_orchestrator."
    "nexora_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
)
def test_nexora_pilot_arc_state_trust_review_pending_without_auto_trust(mock_readiness):
    mock_readiness.return_value = RepoPilotReadinessDashboardResult(
        ok=True,
        session_id="default",
        blockers=[],
    )
    _nexora_arc_stack()
    result = build_nexora_pilot_arc_orchestrator(session_id="fix-195-test")
    report = result.nexora_pilot_arc_orchestrator
    assert report["arc_state"] == "TRUST_REVIEW_PENDING"
    rec = report["sections"]["nexora_trust_recommendation"][0]
    assert rec["trust_status"] == "TRUST_REVIEW_PENDING"
    assert rec["trust_granted_automatically"] is False


def test_run_nexora_pilot_blocked_without_gates():
    outcome = run_nexora_pilot_arc_pilot(pilot_number=1)
    assert outcome.ok is False
    assert "fix_187_expansion_not_approved" in outcome.blockers


@patch(
    "aethos_core.mission_control.nexora_pilot_arc_orchestrator."
    "nexora_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
)
def test_run_nexora_pilot_routes_through_fix_181(mock_readiness):
    mock_readiness.return_value = RepoPilotReadinessDashboardResult(
        ok=True,
        session_id="default",
        blockers=[],
    )
    _seed_nexora_expansion_approval()
    _seed_upstream_trust_baselines()
    with patch(
        "aethos_core.mission_control.end_to_end_repo_development_pilot_harness."
        "end_to_end_repo_development_pilot_harness_service.run_end_to_end_repo_development_pilot",
        return_value=type(
            "Outcome",
            (),
            {
                "ok": True,
                "audit_id": "nexora-audit-1",
                "stages_completed": ["issue_intake"],
                "blockers": [],
            },
        )(),
    ):
        outcome = run_nexora_pilot_arc_pilot(pilot_number=1)
    assert outcome.ok is True
    assert outcome.session_id == NEXORA_PILOT_SESSIONS[0]
    assert outcome.audit_id == "nexora-audit-1"


@patch(
    "aethos_core.mission_control.nexora_pilot_arc_orchestrator."
    "nexora_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
)
def test_chat_route_show_nexora_pilot_arc(mock_readiness):
    mock_readiness.return_value = RepoPilotReadinessDashboardResult(
        ok=True,
        session_id="default",
        blockers=[],
    )
    _nexora_arc_stack()
    turn = resolve_chat_turn("show nexora pilot arc", session_id="fix-195-chat")
    assert turn.intent == "mission_control_nexora_pilot_arc_orchestrator"
    assert (turn.meta or {}).get("route_id") == NEXORA_PILOT_ARC_ORCHESTRATOR_ROUTE_ID


@patch(
    "aethos_core.mission_control.nexora_pilot_arc_orchestrator."
    "nexora_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
)
def test_nexora_pilot_arc_api(mock_readiness):
    mock_readiness.return_value = RepoPilotReadinessDashboardResult(
        ok=True,
        session_id="default",
        blockers=[],
    )
    _nexora_arc_stack()
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/nexora-pilot-arc-orchestrator",
        params={"session_id": "fix-195-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["trust_granting_authority"] is False
    assert payload["nexora_pilot_arc_orchestrator"]["arc_state"] == "TRUST_REVIEW_PENDING"


@patch(
    "aethos_core.mission_control.nexora_pilot_arc_orchestrator."
    "nexora_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
)
def test_fix_191_consumes_nexora_pilot_arc(mock_readiness):
    mock_readiness.return_value = RepoPilotReadinessDashboardResult(
        ok=True,
        session_id="default",
        blockers=[],
    )
    _nexora_arc_stack()
    result = build_cross_repository_multi_agent_delivery_validation(session_id="fix-195-test")
    matrix = result.cross_repository_multi_agent_delivery_validation["sections"][
        "cross_repository_validation_matrix"
    ]
    nexora_row = next(r for r in matrix if r.get("repository") == NEXORA_REPOSITORY)
    assert nexora_row["composes_fix_195"] is True
    assert nexora_row["trust_state"] == "TRUST_REVIEW_PENDING"
