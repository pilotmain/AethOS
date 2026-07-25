# SPDX-License-Identifier: Apache-2.0
"""FIX 194 — Atlas Trader trust report freeze tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
    ATLAS_PILOT_SESSIONS,
    ATLAS_TRADER_REPOSITORY,
)
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_contract import (
    ATLAS_TRADER_TRUST_REPORT_FREEZE_ROUTE_ID,
    TRUST_GRANTING_AUTHORITY_FIX_194,
)
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_intent import (
    is_atlas_trader_trust_report_freeze_intent,
    parse_atlas_trader_trust_report_freeze_record_intent,
)
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_service import (
    build_atlas_trader_trust_report_freeze,
)
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_store import (
    append_atlas_trader_trust_report_freeze_record,
    clear_atlas_trader_trust_report_freeze_records_for_tests,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
    build_cross_repository_multi_agent_delivery_validation,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    persist_pilot_run_audit,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_atlas_trader_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_atlas_trader_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()


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
                "stages_satisfied": ["issue_intake", "implementation_plan", "patch_proposal", "pr_open"],
            },
            "blockers": [],
        }
    )


def test_atlas_trust_freeze_intent():
    assert is_atlas_trader_trust_report_freeze_intent("show atlas trust report freeze")
    parsed = parse_atlas_trader_trust_report_freeze_record_intent(
        "atlas trust decision approve: Operator reviewed Atlas Trader pilot arc evidence"
    )
    assert parsed == (
        "human_trust_decision_approve",
        "Operator reviewed Atlas Trader pilot arc evidence",
    )


def test_build_atlas_trust_freeze():
    _seed_atlas_pilot_audits()
    result = build_atlas_trader_trust_report_freeze(session_id="fix-194-test")
    assert result.ok is True
    board = result.atlas_trader_trust_report_freeze
    assert board["trust_granting_authority"] is False
    assert board["pilot_reexecution_performed"] is False
    sections = board["sections"]
    assert sections["atlas_trust_report"]
    assert sections["atlas_evidence_timeline"]
    assert sections["trust_boundary_matrix"]
    assert sections["expansion_recommendation"]


def test_human_trust_decision_updates_status():
    _seed_atlas_pilot_audits()
    append_atlas_trader_trust_report_freeze_record(
        session_id="fix-194-test",
        kind="atlas_trust_report_freeze_artifact",
        content="Atlas Trader Phase 2 evidence baseline frozen",
    )
    append_atlas_trader_trust_report_freeze_record(
        session_id="fix-194-test",
        kind="human_trust_decision_approve",
        content="Operator approves CONDITIONALLY_TRUSTED for bounded Atlas Trader work",
    )
    result = build_atlas_trader_trust_report_freeze(session_id="fix-194-test")
    assert result.atlas_trader_trust_report_freeze["trust_status"] == "CONDITIONALLY_TRUSTED"
    expansion = result.atlas_trader_trust_report_freeze["sections"]["expansion_recommendation"][0]
    assert expansion["recommendation"] == "CONDITIONALLY_EXPAND"


def test_human_trust_reject_sets_not_trusted():
    _seed_atlas_pilot_audits()
    append_atlas_trader_trust_report_freeze_record(
        session_id="fix-194-test",
        kind="human_trust_decision_reject",
        content="Evidence insufficient for Atlas Trader trust",
    )
    result = build_atlas_trader_trust_report_freeze(session_id="fix-194-test")
    assert result.atlas_trader_trust_report_freeze["trust_status"] == "NOT_TRUSTED"


def test_authority_flags():
    assert TRUST_GRANTING_AUTHORITY_FIX_194 is False


def test_chat_route():
    _seed_atlas_pilot_audits()
    turn = resolve_chat_turn("show atlas trader trust freeze", session_id="fix-194-chat")
    assert turn.intent == "mission_control_atlas_trader_trust_report_freeze"
    assert (turn.meta or {}).get("route_id") == ATLAS_TRADER_TRUST_REPORT_FREEZE_ROUTE_ID


def test_api_get_and_record():
    _seed_atlas_pilot_audits()
    client = TestClient(app)
    get_resp = client.get(
        "/api/v1/mission-control/atlas-trader-trust-report-freeze",
        params={"session_id": "fix-194-api", "format": "both"},
    )
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["trust_granting_authority"] is False
    assert body["atlas_trader_trust_report_freeze"]

    post_resp = client.post(
        "/api/v1/mission-control/atlas-trader-trust-report-freeze/record",
        json={
            "session_id": "fix-194-api",
            "kind": "operator_review_note",
            "content": "Reviewed Atlas Trader pilot evidence before trust decision",
        },
    )
    assert post_resp.status_code == 200


def test_fix_191_consumes_atlas_trust_freeze():
    _seed_atlas_pilot_audits()
    append_atlas_trader_trust_report_freeze_record(
        session_id="fix-194-test",
        kind="atlas_trust_report_freeze_artifact",
        content="Atlas trust baseline frozen",
    )
    result = build_cross_repository_multi_agent_delivery_validation(session_id="fix-194-test")
    matrix = result.cross_repository_multi_agent_delivery_validation["sections"][
        "cross_repository_validation_matrix"
    ]
    atlas_row = next(r for r in matrix if r.get("repository") == ATLAS_TRADER_REPOSITORY)
    assert atlas_row["composes_fix_193"] is True
    assert atlas_row["composes_fix_194_trust_freeze"] is True
    assert atlas_row["trust_state"] == "TRUST_REVIEW_PENDING"
