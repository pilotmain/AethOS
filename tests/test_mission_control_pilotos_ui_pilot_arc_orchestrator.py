# SPDX-License-Identifier: Apache-2.0
"""FIX 188 — PilotOS UI pilot arc orchestrator tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
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
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
    AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188,
    PILOTOS_PILOT_SESSIONS,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ROUTE_ID,
    TRUST_TRANSFER_ENABLED_FIX_188,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_intent import (
    is_pilotos_ui_pilot_arc_orchestrator_intent,
    parse_pilotos_ui_pilot_arc_orchestrator_record_intent,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_service import (
    build_pilotos_ui_pilot_arc_orchestrator,
    run_pilotos_ui_pilot_arc_pilot,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
    append_pilotos_ui_pilot_arc_orchestrator_record,
    clear_pilotos_ui_pilot_arc_orchestrator_records_for_tests,
)
from tests.test_mission_control_independent_repository_trust_expansion import _trust_expansion_stack


@pytest.fixture(autouse=True)
def _clean():
    clear_pilotos_ui_pilot_arc_orchestrator_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_pilotos_ui_pilot_arc_orchestrator_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()


def _seed_pilotos_expansion_approval() -> None:
    append_independent_repository_trust_expansion_record(
        session_id="fix-188-test",
        kind="repo_expansion_approval",
        content="Operator approves pilotmain/pilot-os-ui for independent pilot arc",
        repository=PHASE_2_REPOSITORY_ORDER[0],
    )


def _seed_pilotos_pilot_audits() -> None:
    persist_pilot_run_audit(
        {
            "session_id": PILOTOS_PILOT_SESSIONS[0],
            "repo_issue": "pilotmain/pilot-os-ui#1",
            "outcome": "complete",
            "stages_completed": ["issue_intake"],
            "pilot_report": {"stages_satisfied": ["issue_intake", "implementation_plan"]},
            "blockers": [],
        }
    )
    persist_pilot_run_audit(
        {
            "session_id": PILOTOS_PILOT_SESSIONS[1],
            "repo_issue": "pilotmain/pilot-os-ui#1",
            "outcome": "partial",
            "blockers": ["stage_blocked:intent_alignment"],
            "pilot_report": {"stages_pending": ["intent_alignment"]},
        }
    )
    persist_pilot_run_audit(
        {
            "session_id": PILOTOS_PILOT_SESSIONS[2],
            "repo_issue": "pilotmain/pilot-os-ui#1",
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


def _pilotos_arc_stack() -> None:
    _trust_expansion_stack()
    _seed_pilotos_expansion_approval()
    _seed_pilotos_pilot_audits()


def test_pilotos_pilot_arc_intent():
    assert is_pilotos_ui_pilot_arc_orchestrator_intent("show pilotos pilot arc")
    assert not is_pilotos_ui_pilot_arc_orchestrator_intent("auto trust pilotos")


def test_pilot_arc_record_intent():
    parsed = parse_pilotos_ui_pilot_arc_orchestrator_record_intent(
        "pilot arc issue: pilotmain/pilot-os-ui#1"
    )
    assert parsed == ("repo_issue_binding", "pilotmain/pilot-os-ui#1")


def test_build_pilot_arc_unproven_without_expansion():
    result = build_pilotos_ui_pilot_arc_orchestrator(session_id="fix-188-test")
    assert result.ok is True
    report = result.pilotos_ui_pilot_arc_orchestrator
    assert report["arc_state"] == "UNPROVEN"
    assert report["automatic_trust_granting_enabled"] is AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188
    assert report["trust_transfer_enabled"] is TRUST_TRANSFER_ENABLED_FIX_188
    assert "fix_187_expansion_not_approved" in result.blockers


def test_pilot_arc_state_trust_review_pending_without_auto_trust():
    _pilotos_arc_stack()
    result = build_pilotos_ui_pilot_arc_orchestrator(session_id="fix-188-test")
    report = result.pilotos_ui_pilot_arc_orchestrator
    assert report["arc_state"] == "TRUST_REVIEW_PENDING"
    rec = report["sections"]["pilotos_ui_trust_recommendation"][0]
    assert rec["trust_status"] == "PENDING_OPERATOR_REVIEW"
    assert rec["trust_granted_automatically"] is False


def test_operator_trust_decision_required_for_conditionally_trusted():
    _pilotos_arc_stack()
    record, blockers = append_pilotos_ui_pilot_arc_orchestrator_record(
        session_id="fix-188-test",
        kind="pilot_arc_trust_decision",
        content="CONDITIONALLY_TRUSTED — operator review complete",
        metadata={"trust_status": "CONDITIONALLY_TRUSTED"},
    )
    assert not blockers
    assert record
    result = build_pilotos_ui_pilot_arc_orchestrator(session_id="fix-188-test")
    assert result.pilotos_ui_pilot_arc_orchestrator["arc_state"] == "CONDITIONALLY_TRUSTED"


def test_run_pilot_blocked_without_expansion():
    outcome = run_pilotos_ui_pilot_arc_pilot(pilot_number=1)
    assert outcome.ok is False
    assert "fix_187_expansion_not_approved" in outcome.blockers


def test_run_pilot_routes_through_fix_181():
    _pilotos_arc_stack()
    with patch(
        "aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service.run_end_to_end_repo_development_pilot",
        return_value=type(
            "Outcome",
            (),
            {
                "ok": True,
                "audit_id": "pilotos-audit-1",
                "stages_completed": ["issue_intake"],
                "blockers": [],
            },
        )(),
    ):
        outcome = run_pilotos_ui_pilot_arc_pilot(pilot_number=1)
    assert outcome.ok is True
    assert outcome.session_id == PILOTOS_PILOT_SESSIONS[0]
    assert outcome.audit_id == "pilotos-audit-1"


def test_chat_route_show_pilotos_pilot_arc():
    _pilotos_arc_stack()
    turn = resolve_chat_turn("show pilotos pilot arc", session_id="fix-188-chat")
    assert turn.intent == "mission_control_pilotos_ui_pilot_arc_orchestrator"
    assert (turn.meta or {}).get("route_id") == PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ROUTE_ID


def test_pilot_arc_api():
    _pilotos_arc_stack()
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/pilotos-ui-pilot-arc-orchestrator",
        params={"session_id": "fix-188-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["automatic_trust_granting_enabled"] is False
    assert payload["pilotos_ui_pilot_arc_orchestrator"]["arc_state"] == "TRUST_REVIEW_PENDING"
