# SPDX-License-Identifier: Apache-2.0
"""FIX 176 — human lane admission decision."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
    clear_governed_lane_entry_recommendation_records_for_tests,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_store import (
    append_governed_lane_readiness_board_record,
    clear_governed_lane_readiness_board_records_for_tests,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_contract import (
    UPSTREAM_SECTIONS_OWNED_BY_FIX_175,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_intent import (
    is_human_lane_admission_decision_intent,
    parse_human_lane_admission_decision_record_intent,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_service import (
    build_human_lane_admission_decision,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
    clear_human_lane_admission_decision_records_for_tests,
)
from tests.test_mission_control_governed_lane_readiness_board import _lane_board_stack


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
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
        clear_governed_task_execution_coordination_records_for_tests,
    )
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
        clear_gate_routed_package_outcome_review_records_for_tests,
    )
    from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
        clear_human_decision_board_records_for_tests,
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
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
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
    get_settings.cache_clear()
    yield
    clear_for_tests()
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
    get_settings.cache_clear()


def _admission_decision_stack(session: str) -> None:
    _lane_board_stack(session)
    append_governed_lane_readiness_board_record(
        session_id=session,
        kind="lane_readiness_board_artifact",
        content="Board ready for human lane admission decision.",
    )


def test_human_lane_admission_decision_intent():
    assert is_human_lane_admission_decision_intent("lane admission decision")
    assert is_human_lane_admission_decision_intent("human lane admission decision")
    assert not is_human_lane_admission_decision_intent("enter lane now")


def test_human_lane_admission_decision_record_intent_parse():
    parsed = parse_human_lane_admission_decision_record_intent(
        "lane admission decision admit: software_delivery via workspace_verification gate"
    )
    assert parsed == (
        "lane_admission_decision_record",
        "admit: software_delivery via workspace_verification gate",
    )
    rationale = parse_human_lane_admission_decision_record_intent(
        "lane admission rationale: bounded blast radius accepted for Tier 1-2 delivery"
    )
    assert rationale == (
        "decision_rationale_note",
        "bounded blast radius accepted for Tier 1-2 delivery",
    )


def test_human_lane_admission_decision_composes_upstream_not_duplicates():
    session = "mc-hlad-compose-176"
    _admission_decision_stack(session)
    result = build_human_lane_admission_decision(session_id=session)
    assert result.ok is True
    decision = result.human_lane_admission_decision
    section_keys = set(decision.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_175)
    assert decision["composes_upstream_layers_not_duplicates"] is True
    assert decision["sources"]["composes_governed_lane_readiness_board"] is True
    assert decision["human_lane_admission_decision_not_lane_entry_execution"] is True


def test_human_lane_admission_decision_api_readonly():
    session = "mc-hlad-176"
    _admission_decision_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/human-lane-admission-decision",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["lane_entry_execution_performed"] is False
    assert body["lane_admission_executed"] is False
    decision = body["human_lane_admission_decision"]
    assert decision["schema_version"] == "mission_control_human_lane_admission_decision_v1"
    assert "selected_lane_admission_decision" in decision["sections"]
    assert "Human Lane Admission Decision" in body["markdown"]


def test_human_lane_admission_decision_record_persists():
    session = "mc-hlad-record-176"
    _admission_decision_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/human-lane-admission-decision/record",
        json={
            "session_id": session,
            "kind": "lane_admission_decision_record",
            "content": "admit: software_delivery lane via workspace_verification gate",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["human_lane_admission_decision_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/human-lane-admission-decision",
        params={"session_id": session},
    )
    assert get_res.json()["human_lane_admission_decision"]["human_decision_recorded"] is True


def test_human_lane_admission_decision_chat_view_and_record():
    session = "mc-hlad-chat-176"
    _admission_decision_stack(session)
    record = resolve_chat_turn(
        "lane admission decision admit: proceed to workspace_verification gate",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_human_lane_admission_decision"
    assert record.meta.get("lane_entry_execution_performed") == "false"
    assert "Decision recorded" in record.reply

    view = resolve_chat_turn("lane admission decision", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_human_lane_admission_decision"
    assert "Human Lane Admission Decision" in view.reply


def test_human_lane_admission_decision_no_lane_entry_execution():
    session = "mc-hlad-envelope-176"
    _admission_decision_stack(session)
    result = build_human_lane_admission_decision(session_id=session)
    assert result.ok is True
    decision = result.human_lane_admission_decision
    assert decision["lane_entry_execution_performed"] is False
    assert decision["lane_admission_executed"] is False
    assert decision["execution_performed"] is False
    assert decision["gate_bypass_enabled"] is False
    assert len(decision["fix_176_certification_requirements"]) >= 8

    packet = decision["sections"]["lane_admission_decision_packet"][0]
    assert packet.get("lane_entry_execution_performed") is False
    assert packet.get("lane_admission_executed") is False

    for row in decision["sections"]["selected_lane_admission_decision"]:
        assert row.get("lane_entry_execution_performed") is not True
        assert row.get("autonomous_decision") is not True
