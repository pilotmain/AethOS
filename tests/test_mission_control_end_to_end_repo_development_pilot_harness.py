# SPDX-License-Identifier: Apache-2.0
"""FIX 181 — end-to-end repo development pilot harness."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_contract import (
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_ROUTE_ID,
    PILOT_HARNESS_ORIGIN,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_180,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_intent import (
    is_end_to_end_repo_development_pilot_harness_intent,
    is_run_pilot_harness_intent,
    parse_end_to_end_repo_development_pilot_harness_record_intent,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
    build_end_to_end_repo_development_pilot_harness,
    run_end_to_end_repo_development_pilot,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    list_pilot_run_audits,
)
from tests.test_mission_control_governed_chat_command_invocation_from_handoff import _invocation_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.approval_inbox.approval_execution_service import clear_ui_approval_audit_for_tests
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_store import (
        clear_bounded_execution_participation_records_for_tests,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_store import (
        clear_bounded_delivery_work_packages_records_for_tests,
    )
    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_store import (
        clear_execution_handoff_coordination_records_for_tests,
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
    from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
        clear_governed_lane_entry_recommendation_records_for_tests,
    )
    from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_store import (
        clear_governed_lane_readiness_board_records_for_tests,
    )
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
        clear_governed_task_execution_coordination_records_for_tests,
    )
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
        clear_gate_routed_package_outcome_review_records_for_tests,
    )
    from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
        clear_human_decision_board_records_for_tests,
    )
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
        clear_human_lane_admission_decision_records_for_tests,
    )
    from aethos_core.mission_control.mission_authorization.mission_authorization_store import (
        clear_mission_authorization_records_for_tests,
    )
    from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
        clear_operational_memory_records_for_tests,
    )
    from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_store import (
        clear_work_package_readiness_lane_admission_records_for_tests,
    )
    from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch
    from aethos_core.software_delivery.branch_push_store import clear_for_tests as clear_bp
    from aethos_core.software_delivery.github_pr_open_store import clear_for_tests as clear_po
    from aethos_core.software_delivery.github_pr_preflight_store import clear_for_tests as clear_pf
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as clear_plans
    from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as clear_patch
    from aethos_core.software_delivery.pr_draft_store import clear_for_tests as clear_pr
    from aethos_core.software_delivery.workspace_application_store import clear_for_tests as clear_ws
    from aethos_core.software_delivery.workspace_verification_store import clear_for_tests as clear_vfy

    clear_plans()
    clear_branch()
    clear_patch()
    clear_ws()
    clear_vfy()
    clear_pr()
    clear_pf()
    clear_bp()
    clear_po()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_work_package_readiness_lane_admission_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()
    clear_governed_task_execution_coordination_records_for_tests()
    clear_gate_routed_package_outcome_review_records_for_tests()
    clear_governed_lane_entry_recommendation_records_for_tests()
    clear_governed_lane_readiness_board_records_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_plans()
    clear_branch()
    clear_patch()
    clear_ws()
    clear_vfy()
    clear_pr()
    clear_pf()
    clear_bp()
    clear_po()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_work_package_readiness_lane_admission_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()
    clear_governed_task_execution_coordination_records_for_tests()
    clear_gate_routed_package_outcome_review_records_for_tests()
    clear_governed_lane_entry_recommendation_records_for_tests()
    clear_governed_lane_readiness_board_records_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()


def _pilot_harness_stack(session: str) -> None:
    _invocation_stack(session)


def test_end_to_end_repo_development_pilot_harness_intent():
    assert is_end_to_end_repo_development_pilot_harness_intent("show pilot harness")
    assert is_end_to_end_repo_development_pilot_harness_intent("repo development pilot harness")
    assert is_run_pilot_harness_intent("run pilot")
    assert not is_end_to_end_repo_development_pilot_harness_intent("autonomous pilot")
    assert not is_end_to_end_repo_development_pilot_harness_intent("railway mutation")


def test_end_to_end_repo_development_pilot_harness_record_intent_parse():
    parsed = parse_end_to_end_repo_development_pilot_harness_record_intent(
        "pilot artifact: bounded change for pilotmain/AethOS#80"
    )
    assert parsed == ("pilot_artifact", "bounded change for pilotmain/AethOS#80")


def test_end_to_end_repo_development_pilot_harness_composes_upstream_not_duplicates():
    session = "mc-e2erpdph-compose-181"
    _pilot_harness_stack(session)
    result = build_end_to_end_repo_development_pilot_harness(session_id=session)
    assert result.ok is True
    harness = result.end_to_end_repo_development_pilot_harness
    section_keys = set(harness.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_180)
    assert harness["composes_upstream_layers_not_duplicates"] is True
    assert harness["sources"]["composes_governed_chat_command_invocation_from_handoff"] is True
    assert harness["pilot_harness_not_autonomous_execution"] is True
    assert "pilot_stage_status_matrix" in section_keys
    assert harness["autonomous_pipeline_execution_enabled"] is False


def test_end_to_end_repo_development_pilot_harness_api_readonly():
    session = "mc-e2erpdph-181"
    _pilot_harness_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/end-to-end-repo-development-pilot-harness",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["autonomous_pipeline_execution_enabled"] is False
    assert body["railway_mutation_enabled"] is False
    harness = body["end_to_end_repo_development_pilot_harness"]
    assert harness["schema_version"] == "mission_control_end_to_end_repo_development_pilot_harness_v1"
    assert "pilot_stage_status_matrix" in harness["sections"]
    assert "End-to-End Repo Development Pilot Harness" in body["markdown"]


def test_end_to_end_repo_development_pilot_harness_record_persists():
    session = "mc-e2erpdph-record-181"
    _pilot_harness_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/end-to-end-repo-development-pilot-harness/record",
        json={
            "session_id": session,
            "kind": "pilot_artifact",
            "content": "Pilot scope: pilotmain/AethOS#80 documentation-only change",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["end_to_end_repo_development_pilot_harness_memory_only"] is True


def test_run_pilot_routes_through_chat_governance():
    session = "mc-e2erpdph-run-181"
    _pilot_harness_stack(session)
    outcome = run_end_to_end_repo_development_pilot(session_id=session)
    assert outcome.chat_governance_routed is True
    assert outcome.direct_provider_mutation is False
    assert outcome.autonomous_pipeline_execution is False
    assert outcome.audit_id
    assert list_pilot_run_audits(session_id=session)
    assert outcome.pilot_report.get("pilot_harness_not_autonomous_execution") is True
    assert outcome.pilot_report.get("merge_performed") is False
    assert outcome.pilot_report.get("deploy_performed") is False
    if outcome.chat_steps:
        assert all(step.get("chat_governance_routed") for step in outcome.chat_steps)
        assert PILOT_HARNESS_ORIGIN in str(outcome.chat_steps[0].get("governed_chat_message") or "")


def test_run_pilot_chat_intent():
    session = "mc-e2erpdph-chat-181"
    _pilot_harness_stack(session)
    turn = resolve_chat_turn("run pilot", session_id=session)
    assert turn.meta.get("route_id") == END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_ROUTE_ID
    assert turn.meta.get("autonomous_pipeline_execution") == "false"


def test_pilot_pending_commands_use_plan_drafted_not_missing_implementation_plan_field():
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        _pending_chat_commands,
    )
    from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE

    timeline = {
        "plan": {
            "plan_id": "sdplan-test",
            "status": "plan_drafted",
            "governed_plan": {"goal": "doc update"},
            "planning_approved": False,
        }
    }
    pending = _pending_chat_commands(timeline=timeline, repo_issue="pilotmain/AethOS#1", session_id="default")
    assert pending[0][1].startswith("approve implementation planning")
    assert PLANNING_APPROVAL_PHRASE in pending[0][1]
    assert not any(cmd == "create implementation plan" for _, cmd in pending)
