# SPDX-License-Identifier: Apache-2.0
"""FIX 192 — PilotOS UI trust report freeze tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    persist_pilot_run_audit,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
    PILOTOS_PILOT_SESSIONS,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_contract import (
    PILOTOS_UI_TRUST_REPORT_FREEZE_ROUTE_ID,
    TRUST_GRANTING_AUTHORITY_FIX_192,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_intent import (
    is_pilotos_ui_trust_report_freeze_intent,
    parse_pilotos_ui_trust_report_freeze_record_intent,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_service import (
    build_pilotos_ui_trust_report_freeze,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
    append_pilotos_ui_trust_report_freeze_record,
    clear_pilotos_ui_trust_report_freeze_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_pilotos_ui_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_pilotos_ui_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()


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
                "stages_satisfied": ["issue_intake", "implementation_plan", "patch_proposal", "pr_open"],
            },
            "blockers": [],
        }
    )


def test_pilotos_trust_freeze_intent():
    assert is_pilotos_ui_trust_report_freeze_intent("show pilotos trust report freeze")
    parsed = parse_pilotos_ui_trust_report_freeze_record_intent(
        "pilotos trust decision approve: Operator reviewed PilotOS UI pilot arc evidence"
    )
    assert parsed == (
        "human_trust_decision_approve",
        "Operator reviewed PilotOS UI pilot arc evidence",
    )


def test_build_pilotos_trust_freeze():
    _seed_pilotos_pilot_audits()
    result = build_pilotos_ui_trust_report_freeze(session_id="fix-192-test")
    assert result.ok is True
    board = result.pilotos_ui_trust_report_freeze
    assert board["trust_granting_authority"] is False
    assert board["pilot_reexecution_performed"] is False
    sections = board["sections"]
    assert sections["pilotos_ui_trust_report"]
    assert sections["pilotos_ui_evidence_timeline"]
    assert sections["trust_boundary_matrix"]
    assert sections["expansion_recommendation"]


def test_human_trust_decision_updates_status():
    _seed_pilotos_pilot_audits()
    append_pilotos_ui_trust_report_freeze_record(
        session_id="fix-192-test",
        kind="pilotos_trust_report_freeze_artifact",
        content="PilotOS UI Phase 2 evidence baseline frozen",
    )
    append_pilotos_ui_trust_report_freeze_record(
        session_id="fix-192-test",
        kind="human_trust_decision_approve",
        content="Operator approves CONDITIONALLY_TRUSTED for bounded PilotOS UI work",
    )
    result = build_pilotos_ui_trust_report_freeze(session_id="fix-192-test")
    assert result.pilotos_ui_trust_report_freeze["trust_status"] == "CONDITIONALLY_TRUSTED"
    expansion = result.pilotos_ui_trust_report_freeze["sections"]["expansion_recommendation"][0]
    assert expansion["recommendation"] == "CONDITIONALLY_EXPAND"


def test_authority_flags():
    assert TRUST_GRANTING_AUTHORITY_FIX_192 is False


def test_chat_route():
    _seed_pilotos_pilot_audits()
    turn = resolve_chat_turn("show pilotos ui trust freeze", session_id="fix-192-chat")
    assert turn.intent == "mission_control_pilotos_ui_trust_report_freeze"
    assert (turn.meta or {}).get("route_id") == PILOTOS_UI_TRUST_REPORT_FREEZE_ROUTE_ID


def test_api_get_and_record():
    _seed_pilotos_pilot_audits()
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/pilotos-ui-trust-report-freeze",
        params={"session_id": "fix-192-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["trust_granting_authority"] is False
    assert body["pilotos_ui_trust_report_freeze"]

    post_resp = client.post(
        "/api/v1/mission-control/pilotos-ui-trust-report-freeze/record",
        json={
            "session_id": "fix-192-api",
            "kind": "operator_review_note",
            "content": "Reviewed PilotOS UI pilot evidence before trust decision",
        },
    )
    assert post_resp.status_code == 200
