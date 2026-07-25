# SPDX-License-Identifier: Apache-2.0
"""FIX 178 — frozen gate intake preview."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_contract import (
    UPSTREAM_SECTIONS_OWNED_BY_FIX_177,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_intent import (
    is_frozen_gate_intake_preview_intent,
    parse_frozen_gate_intake_preview_record_intent,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_service import (
    build_frozen_gate_intake_preview,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
    clear_frozen_gate_intake_preview_records_for_tests,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
    append_gate_routed_lane_entry_handoff_record,
    clear_gate_routed_lane_entry_handoff_records_for_tests,
)
from tests.test_mission_control_gate_routed_lane_entry_handoff import _handoff_stack


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
    clear_frozen_gate_intake_preview_records_for_tests()
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
    clear_frozen_gate_intake_preview_records_for_tests()
    get_settings.cache_clear()


def _intake_preview_stack(session: str) -> None:
    _handoff_stack(session)
    append_gate_routed_lane_entry_handoff_record(
        session_id=session,
        kind="gate_handoff_artifact",
        content="Handoff packet staged for workspace_verification frozen gate intake preview.",
    )


def test_frozen_gate_intake_preview_intent():
    assert is_frozen_gate_intake_preview_intent("gate intake preview")
    assert is_frozen_gate_intake_preview_intent("frozen gate intake preview")
    assert not is_frozen_gate_intake_preview_intent("run workspace verification")
    assert not is_frozen_gate_intake_preview_intent("bypass gate")


def test_frozen_gate_intake_preview_record_intent_parse():
    parsed = parse_frozen_gate_intake_preview_record_intent(
        "gate intake artifact: preview workspace_verification intake without execution"
    )
    assert parsed == (
        "intake_preview_artifact",
        "preview workspace_verification intake without execution",
    )


def test_frozen_gate_intake_preview_composes_upstream_not_duplicates():
    session = "mc-fgip-compose-178"
    _intake_preview_stack(session)
    result = build_frozen_gate_intake_preview(session_id=session)
    assert result.ok is True
    preview = result.frozen_gate_intake_preview
    section_keys = set(preview.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_177)
    assert preview["composes_upstream_layers_not_duplicates"] is True
    assert preview["sources"]["composes_gate_routed_lane_entry_handoff"] is True
    assert preview["gate_intake_preview_not_gate_execution"] is True
    assert preview["target_gate_id"] == "workspace_verification"
    assert preview["intake_preview_ready"] is True


def test_frozen_gate_intake_preview_api_readonly():
    session = "mc-fgip-178"
    _intake_preview_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/frozen-gate-intake-preview",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["gate_execution_performed"] is False
    assert body["lane_entry_execution_performed"] is False
    preview = body["frozen_gate_intake_preview"]
    assert preview["schema_version"] == "mission_control_frozen_gate_intake_preview_v1"
    assert "intake_preview_packet" in preview["sections"]
    assert "Frozen Gate Intake Preview" in body["markdown"]


def test_frozen_gate_intake_preview_record_persists():
    session = "mc-fgip-record-178"
    _intake_preview_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/frozen-gate-intake-preview/record",
        json={
            "session_id": session,
            "kind": "intake_preview_artifact",
            "content": "Intake preview for workspace_verification gate",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["frozen_gate_intake_preview_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/frozen-gate-intake-preview",
        params={"session_id": session},
    )
    assert get_res.json()["frozen_gate_intake_preview"]["intake_preview_record_count"] >= 1


def test_frozen_gate_intake_preview_chat_view_and_record():
    session = "mc-fgip-chat-178"
    _intake_preview_stack(session)
    record = resolve_chat_turn(
        "gate intake artifact: preview workspace_verification gate intake",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_frozen_gate_intake_preview"
    assert record.meta.get("gate_execution_performed") == "false"
    assert "Gate intake preview record persisted" in record.reply

    view = resolve_chat_turn("gate intake preview", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_frozen_gate_intake_preview"
    assert "Frozen Gate Intake Preview" in view.reply


def test_frozen_gate_intake_preview_no_gate_execution():
    session = "mc-fgip-envelope-178"
    _intake_preview_stack(session)
    result = build_frozen_gate_intake_preview(session_id=session)
    assert result.ok is True
    preview = result.frozen_gate_intake_preview
    assert preview["gate_execution_performed"] is False
    assert preview["lane_entry_execution_performed"] is False
    assert preview["execution_performed"] is False
    assert preview["gate_bypass_enabled"] is False
    assert len(preview["fix_178_certification_requirements"]) >= 8

    packet = preview["sections"]["intake_preview_packet"][0]
    assert packet.get("gate_execution_performed") is False
    assert packet.get("gate_bypass") is False

    shape = preview["sections"]["packet_shape_validation"][0]
    assert shape.get("valid") is True

    commands = preview["sections"]["required_existing_commands"]
    assert any(c.get("command_hint") == "show workspace verification status" for c in commands)
    for row in commands:
        assert row.get("gate_execution_performed") is not True
        assert row.get("executable") is not True

    confirmation = preview["sections"]["lane_entry_confirmation"][0]
    assert confirmation.get("lane_entry_execution_performed") is False
    assert confirmation.get("gate_execution_performed") is False
