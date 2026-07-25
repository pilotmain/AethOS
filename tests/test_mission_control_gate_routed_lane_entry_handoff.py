# SPDX-License-Identifier: Apache-2.0
"""FIX 177 — gate-routed lane entry handoff."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_contract import (
    UPSTREAM_SECTIONS_OWNED_BY_FIX_176,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_intent import (
    is_gate_routed_lane_entry_handoff_intent,
    parse_gate_routed_lane_entry_handoff_record_intent,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_service import (
    build_gate_routed_lane_entry_handoff,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
    clear_gate_routed_lane_entry_handoff_records_for_tests,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
    append_human_lane_admission_decision_record,
    clear_human_lane_admission_decision_records_for_tests,
)
from tests.test_mission_control_human_lane_admission_decision import _admission_decision_stack


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
    clear_gate_routed_lane_entry_handoff_records_for_tests()
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
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    get_settings.cache_clear()


def _handoff_stack(session: str) -> None:
    _admission_decision_stack(session)
    append_human_lane_admission_decision_record(
        session_id=session,
        kind="lane_admission_decision_record",
        content="admit: software_delivery via workspace_verification gate",
    )


def test_gate_routed_lane_entry_handoff_intent():
    assert is_gate_routed_lane_entry_handoff_intent("lane entry handoff")
    assert is_gate_routed_lane_entry_handoff_intent("gate handoff packet")
    assert not is_gate_routed_lane_entry_handoff_intent("enter lane now")
    assert not is_gate_routed_lane_entry_handoff_intent("bypass gate")


def test_gate_routed_lane_entry_handoff_record_intent_parse():
    parsed = parse_gate_routed_lane_entry_handoff_record_intent(
        "gate handoff artifact: deliver to workspace_verification frozen gate"
    )
    assert parsed == (
        "gate_handoff_artifact",
        "deliver to workspace_verification frozen gate",
    )


def test_gate_routed_lane_entry_handoff_composes_upstream_not_duplicates():
    session = "mc-grleh-compose-177"
    _handoff_stack(session)
    result = build_gate_routed_lane_entry_handoff(session_id=session)
    assert result.ok is True
    handoff = result.gate_routed_lane_entry_handoff
    section_keys = set(handoff.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_176)
    assert handoff["composes_upstream_layers_not_duplicates"] is True
    assert handoff["sources"]["composes_human_lane_admission_decision"] is True
    assert handoff["gate_routed_handoff_not_lane_entry_execution"] is True
    assert handoff["target_gate_id"] == "workspace_verification"
    assert handoff["handoff_ready"] is True


def test_gate_routed_lane_entry_handoff_api_readonly():
    session = "mc-grleh-177"
    _handoff_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/gate-routed-lane-entry-handoff",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["lane_entry_execution_performed"] is False
    assert body["lane_admission_executed"] is False
    handoff = body["gate_routed_lane_entry_handoff"]
    assert handoff["schema_version"] == "mission_control_gate_routed_lane_entry_handoff_v1"
    assert "gate_handoff_packet" in handoff["sections"]
    assert "Gate-Routed Lane Entry Handoff" in body["markdown"]


def test_gate_routed_lane_entry_handoff_record_persists():
    session = "mc-grleh-record-177"
    _handoff_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/gate-routed-lane-entry-handoff/record",
        json={
            "session_id": session,
            "kind": "gate_handoff_artifact",
            "content": "Handoff packet for workspace_verification gate validation",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["gate_routed_lane_entry_handoff_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/gate-routed-lane-entry-handoff",
        params={"session_id": session},
    )
    assert get_res.json()["gate_routed_lane_entry_handoff"]["gate_handoff_record_count"] >= 1


def test_gate_routed_lane_entry_handoff_chat_view_and_record():
    session = "mc-grleh-chat-177"
    _handoff_stack(session)
    record = resolve_chat_turn(
        "gate handoff artifact: route admit decision to workspace_verification frozen gate",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_gate_routed_lane_entry_handoff"
    assert record.meta.get("lane_entry_execution_performed") == "false"
    assert "Gate handoff record persisted" in record.reply

    view = resolve_chat_turn("lane entry handoff", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_gate_routed_lane_entry_handoff"
    assert "Gate-Routed Lane Entry Handoff" in view.reply


def test_gate_routed_lane_entry_handoff_no_lane_entry_execution():
    session = "mc-grleh-envelope-177"
    _handoff_stack(session)
    result = build_gate_routed_lane_entry_handoff(session_id=session)
    assert result.ok is True
    handoff = result.gate_routed_lane_entry_handoff
    assert handoff["lane_entry_execution_performed"] is False
    assert handoff["lane_admission_executed"] is False
    assert handoff["execution_performed"] is False
    assert handoff["gate_bypass_enabled"] is False
    assert len(handoff["fix_177_certification_requirements"]) >= 8

    packet = handoff["sections"]["gate_handoff_packet"][0]
    assert packet.get("lane_entry_execution_performed") is False
    assert packet.get("gate_bypass") is False
    assert packet.get("approval_bypass") is False

    for row in handoff["sections"]["gate_validation_requirements"]:
        assert row.get("gate_bypass") is not True
        assert row.get("approval_bypass") is not True
