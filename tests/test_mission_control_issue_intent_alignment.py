# SPDX-License-Identifier: Apache-2.0
"""FIX 184 — issue intent alignment and patch target validation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_contract import (
    ISSUE_INTENT_ALIGNMENT_ROUTE_ID,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_intent import (
    is_issue_intent_alignment_intent,
    parse_issue_intent_alignment_record_intent,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_service import (
    compute_alignment_assessment,
    extract_issue_scope,
    intent_alignment_gate_satisfied,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    append_issue_intent_alignment_record,
    clear_issue_intent_alignment_records_for_tests,
)
from tests.test_mission_control_end_to_end_repo_development_pilot_harness import _pilot_harness_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
        clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    )
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
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()


def test_issue_intent_alignment_intent():
    assert is_issue_intent_alignment_intent("show intent alignment")
    assert is_issue_intent_alignment_intent("patch target validation")
    assert not is_issue_intent_alignment_intent("propose patch files")
    assert not is_issue_intent_alignment_intent("run pilot")


def test_issue_intent_alignment_record_intent_parse():
    parsed = parse_issue_intent_alignment_record_intent(
        "alignment review: operator confirms doc-only scope before patch"
    )
    assert parsed == ("alignment_review_acknowledged", "operator confirms doc-only scope before patch")


def test_extract_issue_scope_from_plan():
    plan = {
        "issue_title": "Add Pilot Execution Log section",
        "issue_body": "Add section to `docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md`",
        "governed_plan": {"goal": "Add Pilot Execution Log section"},
        "affected_files": ["docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"],
    }
    scope = extract_issue_scope(plan=plan)
    assert "docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md" in scope["expected_targets"]
    assert scope["intended_subsystem"] == "documentation"


def test_compute_alignment_assessment_flags_workflow_mismatch():
    plan = {
        "plan_id": "sdplan-dogfood",
        "issue_title": "Add Pilot Execution Log section",
        "issue_body": "Update docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md",
        "affected_files": ["docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"],
        "governed_plan": {"goal": "Add Pilot Execution Log section"},
    }
    timeline = {
        "plan": plan,
        "patch_proposal": {
            "proposed_files": [".github/workflows/ci.yml"],
            "patch_intent": {"summary": "Adjust workflow rerun resolution"},
        },
    }
    assessment = compute_alignment_assessment(plan=plan, timeline=timeline)
    assert assessment.target_validation_status == "misaligned"
    assert assessment.alignment_score < 80
    assert assessment.escalation_required is True
    assert assessment.unrelated_findings


def test_intent_alignment_gate_requires_operator_ack_on_misalignment():
    session = "mc-iia-gate-184"
    plan = {
        "plan_id": "sdplan-gate",
        "issue_title": "Doc update",
        "affected_files": ["docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"],
        "governed_plan": {"goal": "Doc update"},
    }
    timeline = {
        "plan": plan,
        "branch_context": {"branch_name": "pilot/doc"},
        "patch_proposal": {
            "proposed_files": [".github/workflows/ci.yml"],
        },
    }
    assert intent_alignment_gate_satisfied(session_id=session, timeline=timeline) is False
    append_issue_intent_alignment_record(
        session_id=session,
        kind="alignment_review_acknowledged",
        content="operator accepts bounded doc scope despite patch proposal mismatch",
        plan_id="sdplan-gate",
    )
    assert intent_alignment_gate_satisfied(session_id=session, timeline=timeline) is True


def test_pilot_pending_commands_gate_before_patch():
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        _pending_chat_commands,
    )

    session = "mc-iia-pending-184"
    timeline = {
        "plan": {
            "plan_id": "sdplan-pending",
            "status": "planning_approved",
            "planning_approved": True,
            "governed_plan": {"goal": "Add Pilot Execution Log section"},
            "issue_title": "Add Pilot Execution Log section",
            "issue_body": "Add section to docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md",
            "affected_files": [".github/workflows/ci.yml"],
        },
        "branch_context": {"branch_name": "pilot/doc"},
    }
    pending = _pending_chat_commands(
        timeline=timeline, repo_issue="pilotmain/AethOS#1", session_id=session
    )
    assert pending[0][0] == "intent_alignment"
    assert "show intent alignment" in pending[0][1]
    assert not any(stage == "patch_proposal" for stage, _ in pending)


def test_issue_intent_alignment_chat_route():
    session = "mc-iia-chat-184"
    _pilot_harness_stack(session)
    turn = resolve_chat_turn("show intent alignment", session_id=session)
    assert turn.meta.get("route_id") == ISSUE_INTENT_ALIGNMENT_ROUTE_ID
    assert turn.meta.get("patch_execution_performed") == "false"


def test_issue_intent_alignment_api():
    session = "mc-iia-api-184"
    _pilot_harness_stack(session)
    client = TestClient(app)
    response = client.get(
        f"/api/v1/mission-control/issue-intent-alignment?session_id={session}&format=both"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["patch_execution_performed"] is False
    assert payload["alignment_validation_performed"] is True
    board = payload["issue_intent_alignment"]
    assert board["fix"] == "FIX 184"
    section_keys = set(board.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_181)
