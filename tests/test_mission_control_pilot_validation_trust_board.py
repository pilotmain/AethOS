# SPDX-License-Identifier: Apache-2.0
"""FIX 183 — pilot validation and trust board."""

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
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_contract import (
    PILOT_VALIDATION_TRUST_BOARD_ROUTE_ID,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_intent import (
    is_pilot_validation_trust_board_intent,
    parse_pilot_validation_trust_board_record_intent,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_service import (
    build_pilot_validation_trust_board,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_store import (
    clear_pilot_validation_trust_board_records_for_tests,
)
from tests.test_mission_control_end_to_end_repo_development_pilot_harness import _pilot_harness_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_store import (
        clear_frozen_gate_execution_request_adapter_records_for_tests,
    )
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
        clear_frozen_gate_intake_preview_records_for_tests,
    )
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
        clear_gate_routed_lane_entry_handoff_records_for_tests,
    )
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_store import (
        clear_governed_chat_command_invocation_from_handoff_records_for_tests,
    )
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
        clear_human_lane_admission_decision_records_for_tests,
    )
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_pilot_validation_trust_board_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_pilot_validation_trust_board_records_for_tests()
    get_settings.cache_clear()


def _seed_complete_pilot_audit(session: str) -> str:
    audit = persist_pilot_run_audit(
        {
            "session_id": session,
            "repo_issue": "pilotmain/AethOS#1",
            "outcome": "complete",
            "stages_completed": ["pr_open"],
            "chat_steps": [
                {
                    "step_index": 1,
                    "stage": "implementation_plan",
                    "chat_message": "approve implementation planning\nI approve this governed software delivery implementation plan for human review.",
                    "chat_governance_routed": True,
                }
            ],
            "pilot_report": {
                "stages_satisfied": [
                    "issue_intake",
                    "implementation_plan",
                    "implementation_branch",
                    "patch_proposal",
                    "workspace_apply",
                    "workspace_verify",
                    "pr_draft",
                    "github_pr_preflight",
                    "branch_push",
                    "pr_open",
                ],
                "stages_pending": [],
                "evidence_bundle_ok": True,
            },
            "blockers": [],
            "railway_coupling_detected": False,
            "chat_governance_routed": True,
            "direct_provider_mutation": False,
            "autonomous_pipeline_execution": False,
        }
    )
    return str(audit.get("audit_id") or "")


def _validation_stack(session: str) -> None:
    _pilot_harness_stack(session)
    _seed_complete_pilot_audit(session)


def test_pilot_validation_trust_board_intent():
    assert is_pilot_validation_trust_board_intent("show pilot validation")
    assert is_pilot_validation_trust_board_intent("pilot trust board")
    assert not is_pilot_validation_trust_board_intent("run pilot")
    assert not is_pilot_validation_trust_board_intent("rerun pilot")


def test_pilot_validation_trust_board_record_intent_parse():
    parsed = parse_pilot_validation_trust_board_record_intent(
        "validation artifact: dogfood pilot trust review"
    )
    assert parsed == ("validation_artifact", "dogfood pilot trust review")


def test_pilot_validation_trust_board_composes_upstream_not_duplicates():
    session = "mc-pvtb-compose-183"
    _validation_stack(session)
    result = build_pilot_validation_trust_board(session_id=session)
    assert result.ok is True
    board = result.pilot_validation_trust_board
    section_keys = set(board.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_181)
    assert board["validation_composes_audits_only"] is True
    assert board["pilot_reexecution_performed"] is False
    assert board["trust_recommendation"] in {"yes", "conditional", "no"}


def test_pilot_validation_trust_board_metrics_from_audit():
    session = "mc-pvtb-metrics-183"
    audit_id = _seed_complete_pilot_audit(session)
    result = build_pilot_validation_trust_board(session_id=session)
    assert result.ok is True
    board = result.pilot_validation_trust_board
    assert board["focus_audit_id"] == audit_id
    assert board["approval_count"] >= 1
    assert board["human_effort_score"] >= 0
    assert board["sections"]["trust_recommendation"]


def test_pilot_validation_trust_board_api_readonly():
    session = "mc-pvtb-183"
    _validation_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/pilot-validation-trust-board",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["pilot_reexecution_performed"] is False
    assert body["validation_composes_audits_only"] is True
    board = body["pilot_validation_trust_board"]
    assert board["schema_version"] == "mission_control_pilot_validation_trust_board_v1"
    assert "Pilot Validation & Trust Board" in body["markdown"]


def test_pilot_validation_trust_board_chat_view():
    session = "mc-pvtb-chat-183"
    _validation_stack(session)
    turn = resolve_chat_turn("show pilot validation", session_id=session, apply_relational_layer=False)
    assert turn.meta.get("route_id") == PILOT_VALIDATION_TRUST_BOARD_ROUTE_ID
    assert turn.meta.get("pilot_reexecution_performed", "false") == "false"
    assert "Pilot Validation & Trust Board" in turn.reply
