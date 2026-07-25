# SPDX-License-Identifier: Apache-2.0
"""FIX 180 — governed chat command invocation from handoff."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_contract import (
    HANDOFF_INVOCATION_ORIGIN,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_179,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_intent import (
    is_governed_chat_command_invocation_from_handoff_intent,
    is_invoke_handoff_command_intent,
    parse_governed_chat_command_invocation_from_handoff_record_intent,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_service import (
    build_governed_chat_command_invocation_from_handoff,
    invoke_governed_chat_command_from_handoff,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_store import (
    clear_governed_chat_command_invocation_from_handoff_records_for_tests,
    list_handoff_invocation_audits,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_store import (
    clear_frozen_gate_execution_request_adapter_records_for_tests,
)
from tests.test_mission_control_frozen_gate_execution_request_adapter import _execution_request_stack


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
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
        clear_frozen_gate_intake_preview_records_for_tests,
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
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
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
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    get_settings.cache_clear()


def _invocation_stack(session: str) -> None:
    _execution_request_stack(session)


def test_governed_chat_command_invocation_from_handoff_intent():
    assert is_governed_chat_command_invocation_from_handoff_intent("governed handoff invocation")
    assert is_governed_chat_command_invocation_from_handoff_intent("handoff command invocation")
    assert is_invoke_handoff_command_intent("invoke handoff command")
    assert not is_governed_chat_command_invocation_from_handoff_intent("bypass gate")
    assert not is_governed_chat_command_invocation_from_handoff_intent("direct provider")


def test_governed_chat_command_invocation_from_handoff_record_intent_parse():
    parsed = parse_governed_chat_command_invocation_from_handoff_record_intent(
        "handoff invocation artifact: route workspace_verification through chat governance"
    )
    assert parsed == (
        "invocation_artifact",
        "route workspace_verification through chat governance",
    )


def test_governed_chat_command_invocation_from_handoff_composes_upstream_not_duplicates():
    session = "mc-gccifh-compose-180"
    _invocation_stack(session)
    result = build_governed_chat_command_invocation_from_handoff(session_id=session)
    assert result.ok is True
    invocation = result.governed_chat_command_invocation_from_handoff
    section_keys = set(invocation.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_179)
    assert invocation["composes_upstream_layers_not_duplicates"] is True
    assert invocation["sources"]["composes_frozen_gate_execution_request_adapter"] is True
    assert invocation["handoff_invocation_not_direct_execution"] is True
    assert invocation["frozen_chat_command"] == "run workspace verification"
    assert invocation["invocation_ready"] is True


def test_governed_chat_command_invocation_from_handoff_api_readonly():
    session = "mc-gccifh-180"
    _invocation_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governed-chat-command-invocation-from-handoff",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["direct_execution_performed"] is False
    assert body["direct_provider_mutation_performed"] is False
    invocation = body["governed_chat_command_invocation_from_handoff"]
    assert invocation["schema_version"] == "mission_control_governed_chat_command_invocation_from_handoff_v1"
    assert "governed_invocation_packet" in invocation["sections"]
    assert "Governed Chat Command Invocation From Handoff" in body["markdown"]


def test_governed_chat_command_invocation_from_handoff_record_persists():
    session = "mc-gccifh-record-180"
    _invocation_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governed-chat-command-invocation-from-handoff/record",
        json={
            "session_id": session,
            "kind": "invocation_artifact",
            "content": "Invocation packet for workspace_verification chat route",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["governed_chat_command_invocation_from_handoff_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/governed-chat-command-invocation-from-handoff",
        params={"session_id": session},
    )
    assert get_res.json()["governed_chat_command_invocation_from_handoff"]["invocation_record_count"] >= 1


def test_governed_chat_command_invocation_from_handoff_invoke_routes_through_chat():
    session = "mc-gccifh-invoke-180"
    _invocation_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governed-chat-command-invocation-from-handoff/invoke",
        json={"session_id": session},
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["chat_governance_routed"] is True
    assert body["direct_provider_mutation_performed"] is False
    assert body["handoff_invocation_origin"] == HANDOFF_INVOCATION_ORIGIN
    assert body["frozen_chat_command"] == "run workspace verification"
    assert body["route_id"]
    assert body["audit_id"]
    audits = list_handoff_invocation_audits(session_id=session)
    assert len(audits) >= 1
    assert audits[0].get("direct_provider_mutation") is False
    assert audits[0].get("chat_governance_routed") is True


def test_governed_chat_command_invocation_from_handoff_chat_view_and_invoke():
    session = "mc-gccifh-chat-180"
    _invocation_stack(session)
    record = resolve_chat_turn(
        "handoff invocation artifact: prepare workspace_verification chat invocation",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_governed_chat_command_invocation_from_handoff"
    assert record.meta.get("direct_provider_mutation_performed") == "false"
    assert "Handoff invocation record persisted" in record.reply

    view = resolve_chat_turn("governed handoff invocation", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_governed_chat_command_invocation_from_handoff"
    assert "Governed Chat Command Invocation From Handoff" in view.reply

    invoke = resolve_chat_turn("invoke handoff command", session_id=session, apply_relational_layer=False)
    assert invoke.meta.get("route_id") == "mission_control_governed_chat_command_invocation_from_handoff"
    assert invoke.meta.get("chat_governance_routed") == "true"
    assert invoke.meta.get("direct_provider_mutation_performed") == "false"
    assert "Handoff command invoked through chat governance" in invoke.reply


def test_governed_chat_command_invocation_from_handoff_no_direct_execution():
    session = "mc-gccifh-envelope-180"
    _invocation_stack(session)
    result = build_governed_chat_command_invocation_from_handoff(session_id=session)
    assert result.ok is True
    invocation = result.governed_chat_command_invocation_from_handoff
    assert invocation["direct_execution_performed"] is False
    assert invocation["direct_provider_mutation_performed"] is False
    assert invocation["hidden_command_execution_performed"] is False
    assert invocation["gate_bypass_enabled"] is False
    assert len(invocation["fix_180_certification_requirements"]) >= 8

    packet = invocation["sections"]["governed_invocation_packet"][0]
    assert packet.get("direct_execution_performed") is False
    assert packet.get("direct_provider_mutation_performed") is False

    build_row = invocation["sections"]["frozen_chat_command_build"][0]
    assert build_row.get("frozen_chat_command") == "run workspace verification"
    assert HANDOFF_INVOCATION_ORIGIN in str(build_row.get("governed_chat_message") or "")

    outcome = invoke_governed_chat_command_from_handoff(session_id=session)
    assert outcome.ok is True
    assert outcome.chat_governance_routed is True
    assert outcome.direct_provider_mutation is False
    assert outcome.route_id != "mission_control_governed_chat_command_invocation_from_handoff"
