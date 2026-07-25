# SPDX-License-Identifier: Apache-2.0
"""FIX 174 — governed lane entry recommendation (composes FIX 169 + FIX 173)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
    append_gate_routed_package_outcome_review_record,
    clear_gate_routed_package_outcome_review_records_for_tests,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_contract import (
    UPSTREAM_SECTIONS_OWNED_BY_FIX_169,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_173,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_intent import (
    is_governed_lane_entry_recommendation_intent,
    parse_governed_lane_entry_recommendation_record_intent,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_service import (
    build_governed_lane_entry_recommendation,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
    clear_governed_lane_entry_recommendation_records_for_tests,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
    append_governed_task_execution_coordination_record,
    clear_governed_task_execution_coordination_records_for_tests,
)
from tests.test_mission_control_gate_routed_package_outcome_review import _gate_review_stack


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
    get_settings.cache_clear()


def test_governed_lane_entry_recommendation_intent():
    assert is_governed_lane_entry_recommendation_intent("show lane recommendation")
    assert is_governed_lane_entry_recommendation_intent("lane entry recommendation")
    assert not is_governed_lane_entry_recommendation_intent("enter lane now")


def test_governed_lane_entry_recommendation_record_intent_parse():
    parsed = parse_governed_lane_entry_recommendation_record_intent(
        "lane recommendation artifact: recommend workspace_verification after gate review"
    )
    assert parsed == (
        "lane_recommendation_artifact",
        "recommend workspace_verification after gate review",
    )


def test_governed_lane_entry_recommendation_composes_upstream_not_duplicates():
    session = "mc-gler-compose-174"
    _gate_review_stack(session)
    result = build_governed_lane_entry_recommendation(session_id=session)
    assert result.ok is True
    rec = result.governed_lane_entry_recommendation
    section_keys = set(rec.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_169)
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_173)
    assert rec["composes_upstream_layers_not_duplicates"] is True
    assert rec["sources"]["composes_work_package_readiness_lane_admission"] is True
    assert rec["sources"]["composes_gate_routed_package_outcome_review"] is True
    assert "readiness_upstream_read" in section_keys
    assert "gate_review_upstream_read" in section_keys
    assert rec["lane_recommendation_not_admission_authority"] is True


def test_governed_lane_entry_recommendation_api_readonly():
    session = "mc-gler-174"
    _gate_review_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governed-lane-entry-recommendation",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["execution_performed"] is False
    assert body["lane_admission_performed"] is False
    assert body["gate_bypass_enabled"] is False
    rec = body["governed_lane_entry_recommendation"]
    assert rec["schema_version"] == "mission_control_governed_lane_entry_recommendation_v1"
    assert "lane_entry_candidates" in rec["sections"]
    assert "Governed Lane Entry Recommendation" in body["markdown"]


def test_governed_lane_entry_recommendation_record_persists():
    session = "mc-gler-record-174"
    _gate_review_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governed-lane-entry-recommendation/record",
        json={
            "session_id": session,
            "kind": "lane_recommendation_artifact",
            "content": "Recommend software_delivery lane via workspace_verification gate.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["governed_lane_entry_recommendation_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/governed-lane-entry-recommendation",
        params={"session_id": session},
    )
    assert get_res.json()["governed_lane_entry_recommendation"]["lane_recommendation_record_count"] == 1


def test_governed_lane_entry_recommendation_chat_view_and_record():
    session = "mc-gler-chat-174"
    _gate_review_stack(session)
    record = resolve_chat_turn(
        "lane recommendation artifact: eligible for workspace_verification gate",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_governed_lane_entry_recommendation"
    assert record.meta.get("lane_admission_performed") == "false"
    assert "Recommendation only" in record.reply

    view = resolve_chat_turn("lane entry recommendation", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_governed_lane_entry_recommendation"
    assert "Governed Lane Entry Recommendation" in view.reply


def test_governed_lane_entry_recommendation_no_admission_authority():
    session = "mc-gler-envelope-174"
    _gate_review_stack(session)
    append_gate_routed_package_outcome_review_record(
        session_id=session,
        kind="gate_review_artifact",
        content="Gate review complete for lane recommendation.",
    )
    result = build_governed_lane_entry_recommendation(session_id=session)
    assert result.ok is True
    rec = result.governed_lane_entry_recommendation
    assert rec["execution_performed"] is False
    assert rec["lane_admission_performed"] is False
    assert rec["autonomous_lane_entry_enabled"] is False
    assert rec["gate_bypass_enabled"] is False
    assert len(rec["fix_174_certification_requirements"]) >= 8

    for row in rec["sections"]["lane_entry_candidates"]:
        assert row.get("lane_admission_performed") is not True
        assert row.get("lane_entry") is not True
        assert row.get("gate_bypass") is not True

    for row in rec["sections"]["recommended_next_gate"]:
        assert row.get("lane_admission_performed") is not True
        assert row.get("gate_bypass") is not True
