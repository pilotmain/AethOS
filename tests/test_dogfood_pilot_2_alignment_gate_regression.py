# SPDX-License-Identifier: Apache-2.0
"""Dogfood pilot 2 — FIX 184 alignment gate regression on issue #1 drift pattern."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
    _pending_chat_commands,
    build_end_to_end_repo_development_pilot_harness,
    run_end_to_end_repo_development_pilot,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    append_end_to_end_repo_development_pilot_harness_record,
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    list_pilot_run_audits,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_contract import (
    ALIGNMENT_ESCALATION_THRESHOLD,
    ISSUE_INTENT_ALIGNMENT_ROUTE_ID,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_service import (
    build_issue_intent_alignment,
    compute_alignment_assessment,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    clear_issue_intent_alignment_records_for_tests,
)
from aethos_core.software_delivery.branch_orchestration_store import save_branch_context
from aethos_core.software_delivery.issue_plan_store import save_issue_plan
from aethos_core.software_delivery.patch_proposal_store import save_patch_proposal
from tests.test_mission_control_end_to_end_repo_development_pilot_harness import _pilot_harness_stack

SESSION = "dogfood-pilot-2"
REPO_ISSUE = "pilotmain/AethOS#1"
DOC_TARGET = "docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"
DRIFT_TARGET = "aethos_core/mission_control/mission_control_router.py"


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
    from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests
    from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as clear_patch

    clear_for_tests()
    clear_branch()
    clear_patch()
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
    clear_branch()
    clear_patch()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()


def _drift_timeline_dict(*, plan_id: str) -> dict:
    plan = {
        "plan_id": plan_id,
        "session_id": SESSION,
        "status": "planning_approved",
        "planning_approved": True,
        "issue_title": "AethOS Dogfood Pilot — Add Pilot Execution Log Section",
        "issue_body": f"Add section to `{DOC_TARGET}` — Pilot Execution Log table.",
        "affected_files": [DRIFT_TARGET],
        "governed_plan": {
            "goal": "Add Pilot Execution Log section to dogfood validation principle doc",
            "scope": DOC_TARGET,
        },
    }
    return {
        "plan": plan,
        "branch_context": {
            "branch_context_id": "sdbc-dogfood-pilot-2",
            "plan_id": plan_id,
            "branch_name": "pilot/dogfood-pilot-2-log",
        },
        "patch_proposal": {
            "proposal_id": "sdpp-dogfood-pilot-2",
            "plan_id": plan_id,
            "status": "files_proposed",
            "proposed_files": [DRIFT_TARGET],
            "patch_proposal_approved": False,
            "patch_intent": {"summary": "Adjust workflow rerun resolution"},
        },
    }


def _persist_dogfood_pilot_2_drift_state(*, session: str) -> str:
    _pilot_harness_stack(session)
    append_end_to_end_repo_development_pilot_harness_record(
        session_id=session,
        kind="pilot_issue_note",
        content=REPO_ISSUE,
    )
    append_end_to_end_repo_development_pilot_harness_record(
        session_id=session,
        kind="pilot_artifact",
        content="dogfood-pilot-2 alignment gate regression",
    )
    harness = build_end_to_end_repo_development_pilot_harness(session_id=session)
    plan_id = str(harness.end_to_end_repo_development_pilot_harness.get("plan_id") or "sdplan-dogfood-pilot-2")

    save_issue_plan(
        {
            "plan_id": plan_id,
            "session_id": session,
            "status": "planning_approved",
            "planning_approved": True,
            "issue_title": "AethOS Dogfood Pilot — Add Pilot Execution Log Section",
            "issue_body": f"Add section to `{DOC_TARGET}` — Pilot Execution Log table.",
            "affected_files": [DRIFT_TARGET],
            "governed_plan": {
                "goal": "Add Pilot Execution Log section to dogfood validation principle doc",
                "scope": DOC_TARGET,
            },
        }
    )
    save_branch_context(
        {
            "branch_context_id": "sdbc-dogfood-pilot-2",
            "plan_id": plan_id,
            "session_id": session,
            "branch_name": "pilot/dogfood-pilot-2-log",
            "workspace_path": str(
                __import__(
                    "aethos_core.software_delivery.branch_orchestration_store",
                    fromlist=["workspace_path_for_plan"],
                ).workspace_path_for_plan(plan_id=plan_id)
            ),
        }
    )
    save_patch_proposal(
        {
            "proposal_id": "sdpp-dogfood-pilot-2",
            "plan_id": plan_id,
            "session_id": session,
            "branch_context_id": "sdbc-dogfood-pilot-2",
            "status": "files_proposed",
            "proposed_files": [DRIFT_TARGET],
            "patch_proposal_approved": False,
            "patch_intent": {"summary": "Adjust workflow rerun resolution"},
            "unified_diffs": [],
            "events": [],
        }
    )
    return plan_id


def test_dogfood_pilot_2_alignment_detects_wrong_targets():
    plan_id = _persist_dogfood_pilot_2_drift_state(session=SESSION)
    timeline = _drift_timeline_dict(plan_id=plan_id)
    assessment = compute_alignment_assessment(plan=timeline["plan"], timeline=timeline)

    assert DOC_TARGET in assessment.expected_targets
    assert DRIFT_TARGET in assessment.actual_targets
    assert assessment.alignment_score < ALIGNMENT_ESCALATION_THRESHOLD
    assert assessment.escalation_required is True
    assert assessment.unrelated_findings
    assert assessment.target_validation_status in {"misaligned", "partially_aligned"}


def test_dogfood_pilot_2_pending_commands_pause_before_patch_approval():
    plan_id = _persist_dogfood_pilot_2_drift_state(session=SESSION)
    timeline = _drift_timeline_dict(plan_id=plan_id)
    pending = _pending_chat_commands(timeline=timeline, repo_issue=REPO_ISSUE, session_id=SESSION)

    assert pending[0][0] == "intent_alignment"
    assert "show intent alignment" in pending[0][1] or "alignment review" in pending[0][1]
    assert not any(stage == "patch_proposal" and "approve patch" in cmd for stage, cmd in pending)


def test_dogfood_pilot_2_run_pilot_stops_at_intent_alignment():
    _persist_dogfood_pilot_2_drift_state(session=SESSION)
    outcome = run_end_to_end_repo_development_pilot(session_id=SESSION, repo_issue=REPO_ISSUE)
    assert outcome.ok is False
    assert outcome.chat_steps
    assert outcome.chat_steps[0].get("stage") == "intent_alignment"
    assert "patch_proposal" not in outcome.stages_completed
    assert outcome.chat_steps[0].get("direct_provider_mutation") is False

    audits = list_pilot_run_audits(session_id=SESSION)
    assert audits
    assert audits[-1].get("outcome") == "partial"


def test_dogfood_pilot_2_show_intent_alignment_route():
    _persist_dogfood_pilot_2_drift_state(session=SESSION)
    turn = resolve_chat_turn("show intent alignment", session_id=SESSION)
    assert turn.meta.get("route_id") == ISSUE_INTENT_ALIGNMENT_ROUTE_ID
    assert turn.meta.get("patch_execution_performed") == "false"
    assert turn.meta.get("escalation_required") == "true"


def test_dogfood_pilot_2_alignment_board_receipts():
    _persist_dogfood_pilot_2_drift_state(session=SESSION)
    result = build_issue_intent_alignment(session_id=SESSION)
    assert result.ok is True
    board = result.issue_intent_alignment
    assert board["patch_execution_performed"] is False
    assert board["escalation_required"] is True
    assert board["alignment_score"] < ALIGNMENT_ESCALATION_THRESHOLD
    assert board["intent_alignment_gate_satisfied"] is False
    sections = board["sections"]
    assert sections["misalignment_findings"]
    assert sections["escalation_rules"][0]["human_reengagement_required"] is True


def test_dogfood_pilot_2_no_hidden_execution_after_gate():
    plan_id = _persist_dogfood_pilot_2_drift_state(session=SESSION)
    timeline = _drift_timeline_dict(plan_id=plan_id)
    pending = _pending_chat_commands(timeline=timeline, repo_issue=REPO_ISSUE, session_id=SESSION)
    assert pending[0][0] == "intent_alignment"
    assert not any("apply approved patch" in cmd for _, cmd in pending)
