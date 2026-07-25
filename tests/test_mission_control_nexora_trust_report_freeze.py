# SPDX-License-Identifier: Apache-2.0
"""FIX 196 — Nexora trust report freeze tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
    build_cross_repository_multi_agent_delivery_validation,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    persist_pilot_run_audit,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_contract import (
    NEXORA_PILOT_SESSIONS,
    NEXORA_REPOSITORY,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_contract import (
    NEXORA_TRUST_REPORT_FREEZE_ROUTE_ID,
    TRUST_GRANTING_AUTHORITY_FIX_196,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_intent import (
    is_nexora_trust_report_freeze_intent,
    parse_nexora_trust_report_freeze_record_intent,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_service import (
    build_nexora_trust_report_freeze,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_store import (
    append_nexora_trust_report_freeze_record,
    clear_nexora_trust_report_freeze_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_nexora_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_nexora_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()


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


def test_nexora_trust_freeze_intent():
    assert is_nexora_trust_report_freeze_intent("show nexora trust report freeze")
    parsed = parse_nexora_trust_report_freeze_record_intent(
        "nexora trust decision approve: Operator reviewed Nexora pilot arc evidence"
    )
    assert parsed == (
        "human_trust_decision_approve",
        "Operator reviewed Nexora pilot arc evidence",
    )


def test_build_nexora_trust_freeze():
    _seed_nexora_pilot_audits()
    result = build_nexora_trust_report_freeze(session_id="fix-196-test")
    assert result.ok is True
    board = result.nexora_trust_report_freeze
    assert board["trust_granting_authority"] is False
    assert board["pilot_reexecution_performed"] is False
    sections = board["sections"]
    assert sections["nexora_trust_report"]
    assert sections["nexora_evidence_timeline"]
    assert sections["trust_boundary_matrix"]
    assert sections["expansion_recommendation"]


def test_human_trust_decision_updates_status():
    _seed_nexora_pilot_audits()
    append_nexora_trust_report_freeze_record(
        session_id="fix-196-test",
        kind="nexora_trust_report_freeze_artifact",
        content="Nexora Phase 2 evidence baseline frozen",
    )
    append_nexora_trust_report_freeze_record(
        session_id="fix-196-test",
        kind="human_trust_decision_approve",
        content="Operator approves CONDITIONALLY_TRUSTED for bounded Nexora work",
    )
    result = build_nexora_trust_report_freeze(session_id="fix-196-test")
    assert result.nexora_trust_report_freeze["trust_status"] == "CONDITIONALLY_TRUSTED"
    assert result.nexora_trust_report_freeze["multi_repo_trust_baseline_complete"] is True
    expansion = result.nexora_trust_report_freeze["sections"]["expansion_recommendation"][0]
    assert expansion["recommendation"] == "CONDITIONALLY_EXPAND"
    assert expansion["multi_repo_trust_baseline_complete"] is True


def test_human_trust_reject_sets_not_trusted():
    _seed_nexora_pilot_audits()
    append_nexora_trust_report_freeze_record(
        session_id="fix-196-test",
        kind="human_trust_decision_reject",
        content="Evidence insufficient for Nexora trust",
    )
    result = build_nexora_trust_report_freeze(session_id="fix-196-test")
    assert result.nexora_trust_report_freeze["trust_status"] == "NOT_TRUSTED"


def test_authority_flags():
    assert TRUST_GRANTING_AUTHORITY_FIX_196 is False


def test_chat_route():
    _seed_nexora_pilot_audits()
    turn = resolve_chat_turn("show nexora trust freeze", session_id="fix-196-chat")
    assert turn.intent == "mission_control_nexora_trust_report_freeze"
    assert (turn.meta or {}).get("route_id") == NEXORA_TRUST_REPORT_FREEZE_ROUTE_ID


def test_api_get_and_record():
    _seed_nexora_pilot_audits()
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/nexora-trust-report-freeze",
        params={"session_id": "fix-196-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["trust_granting_authority"] is False
    assert body["nexora_trust_report_freeze"]

    post_resp = client.post(
        "/api/v1/mission-control/nexora-trust-report-freeze/record",
        json={
            "session_id": "fix-196-api",
            "kind": "operator_review_note",
            "content": "Reviewed Nexora pilot evidence before trust decision",
        },
    )
    assert post_resp.status_code == 200


def test_fix_191_consumes_nexora_trust_freeze():
    _seed_nexora_pilot_audits()
    append_nexora_trust_report_freeze_record(
        session_id="fix-196-test",
        kind="nexora_trust_report_freeze_artifact",
        content="Nexora trust baseline frozen",
    )
    append_nexora_trust_report_freeze_record(
        session_id="fix-196-test",
        kind="human_trust_decision_approve",
        content="Operator approves Nexora trust after review",
    )
    result = build_cross_repository_multi_agent_delivery_validation(session_id="fix-196-test")
    matrix = result.cross_repository_multi_agent_delivery_validation["sections"][
        "cross_repository_validation_matrix"
    ]
    nexora_row = next(r for r in matrix if r.get("repository") == NEXORA_REPOSITORY)
    assert nexora_row["composes_fix_195"] is True
    assert nexora_row["composes_fix_196_trust_freeze"] is True
    assert nexora_row["trust_state"] == "CONDITIONALLY_TRUSTED"
