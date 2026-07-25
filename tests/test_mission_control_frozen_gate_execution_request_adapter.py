# SPDX-License-Identifier: Apache-2.0
"""FIX 179 — frozen gate execution request adapter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_contract import (
    UPSTREAM_SECTIONS_OWNED_BY_FIX_178,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_intent import (
    is_frozen_gate_execution_request_adapter_intent,
    parse_frozen_gate_execution_request_adapter_record_intent,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_service import (
    build_frozen_gate_execution_request_adapter,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_store import (
    append_frozen_gate_execution_request_adapter_record,
    clear_frozen_gate_execution_request_adapter_records_for_tests,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
    clear_frozen_gate_intake_preview_records_for_tests,
)
from tests.test_mission_control_frozen_gate_intake_preview import _intake_preview_stack


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
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
        clear_gate_routed_lane_entry_handoff_records_for_tests,
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
    clear_frozen_gate_execution_request_adapter_records_for_tests()
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
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    get_settings.cache_clear()


def _execution_request_stack(session: str) -> None:
    _intake_preview_stack(session)


def test_frozen_gate_execution_request_adapter_intent():
    assert is_frozen_gate_execution_request_adapter_intent("gate execution request")
    assert is_frozen_gate_execution_request_adapter_intent("execution request adapter")
    assert not is_frozen_gate_execution_request_adapter_intent("run workspace verification")
    assert not is_frozen_gate_execution_request_adapter_intent("execute gate")


def test_frozen_gate_execution_request_adapter_record_intent_parse():
    parsed = parse_frozen_gate_execution_request_adapter_record_intent(
        "gate execution request artifact: map workspace_verification to run workspace verification"
    )
    assert parsed == (
        "execution_request_artifact",
        "map workspace_verification to run workspace verification",
    )


def test_frozen_gate_execution_request_adapter_composes_upstream_not_duplicates():
    session = "mc-fgera-compose-179"
    _execution_request_stack(session)
    result = build_frozen_gate_execution_request_adapter(session_id=session)
    assert result.ok is True
    adapter = result.frozen_gate_execution_request_adapter
    section_keys = set(adapter.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_178)
    assert adapter["composes_upstream_layers_not_duplicates"] is True
    assert adapter["sources"]["composes_frozen_gate_intake_preview"] is True
    assert adapter["execution_request_not_command_execution"] is True
    assert adapter["target_gate_id"] == "workspace_verification"
    assert adapter["primary_frozen_command"] == "run workspace verification"
    assert adapter["execution_request_ready"] is True


def test_frozen_gate_execution_request_adapter_api_readonly():
    session = "mc-fgera-179"
    _execution_request_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/frozen-gate-execution-request-adapter",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["command_execution_performed"] is False
    assert body["gate_execution_performed"] is False
    adapter = body["frozen_gate_execution_request_adapter"]
    assert adapter["schema_version"] == "mission_control_frozen_gate_execution_request_adapter_v1"
    assert "gate_execution_request_artifact" in adapter["sections"]
    assert "Frozen Gate Execution Request Adapter" in body["markdown"]


def test_frozen_gate_execution_request_adapter_record_persists():
    session = "mc-fgera-record-179"
    _execution_request_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/frozen-gate-execution-request-adapter/record",
        json={
            "session_id": session,
            "kind": "execution_request_artifact",
            "content": "Request run workspace verification via frozen lane command",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["frozen_gate_execution_request_adapter_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/frozen-gate-execution-request-adapter",
        params={"session_id": session},
    )
    assert get_res.json()["frozen_gate_execution_request_adapter"]["execution_request_record_count"] >= 1


def test_frozen_gate_execution_request_adapter_chat_view_and_record():
    session = "mc-fgera-chat-179"
    _execution_request_stack(session)
    record = resolve_chat_turn(
        "gate execution request artifact: request workspace_verification frozen command",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_frozen_gate_execution_request_adapter"
    assert record.meta.get("command_execution_performed") == "false"
    assert "Gate execution request record persisted" in record.reply

    view = resolve_chat_turn("gate execution request", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_frozen_gate_execution_request_adapter"
    assert "Frozen Gate Execution Request Adapter" in view.reply


def test_frozen_gate_execution_request_adapter_no_command_execution():
    session = "mc-fgera-envelope-179"
    _execution_request_stack(session)
    result = build_frozen_gate_execution_request_adapter(session_id=session)
    assert result.ok is True
    adapter = result.frozen_gate_execution_request_adapter
    assert adapter["command_execution_performed"] is False
    assert adapter["gate_execution_performed"] is False
    assert adapter["execution_performed"] is False
    assert adapter["gate_bypass_enabled"] is False
    assert len(adapter["fix_179_certification_requirements"]) >= 8

    artifact = adapter["sections"]["gate_execution_request_artifact"][0]
    assert artifact.get("command_execution_performed") is False
    assert artifact.get("approval_bypass") is False

    mapping = adapter["sections"]["frozen_gate_command_mapping"][0]
    assert mapping.get("primary_frozen_command") == "run workspace verification"

    audit = adapter["sections"]["audit_replay_linkage"][0]
    assert audit.get("timeline_link_ref")
    assert audit.get("replay_link_key")

    phrases = adapter["sections"]["approval_phrase_preservation"][0]
    assert phrases.get("approval_bypass") is False
