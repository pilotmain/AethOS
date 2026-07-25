# SPDX-License-Identifier: Apache-2.0
"""FIX 175 — governed lane readiness board (composes FIX 174)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
    append_governed_lane_entry_recommendation_record,
    clear_governed_lane_entry_recommendation_records_for_tests,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_contract import (
    UPSTREAM_SECTIONS_OWNED_BY_FIX_170,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_174,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_intent import (
    is_governed_lane_readiness_board_intent,
    parse_governed_lane_readiness_board_record_intent,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_service import (
    build_governed_lane_readiness_board,
)
from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_store import (
    clear_governed_lane_readiness_board_records_for_tests,
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
    get_settings.cache_clear()


def _lane_board_stack(session: str) -> None:
    _gate_review_stack(session)
    append_governed_lane_entry_recommendation_record(
        session_id=session,
        kind="lane_recommendation_artifact",
        content="Lane recommendation ready for readiness board.",
    )


def test_governed_lane_readiness_board_intent():
    assert is_governed_lane_readiness_board_intent("lane readiness board")
    assert is_governed_lane_readiness_board_intent("show lane readiness board")
    assert not is_governed_lane_readiness_board_intent("lane admission now")


def test_governed_lane_readiness_board_record_intent_parse():
    parsed = parse_governed_lane_readiness_board_record_intent(
        "lane readiness board artifact: consolidate candidates and blockers for human review"
    )
    assert parsed == (
        "lane_readiness_board_artifact",
        "consolidate candidates and blockers for human review",
    )


def test_governed_lane_readiness_board_composes_upstream_not_duplicates():
    session = "mc-glrb-compose-175"
    _lane_board_stack(session)
    result = build_governed_lane_readiness_board(session_id=session)
    assert result.ok is True
    board = result.governed_lane_readiness_board
    section_keys = set(board.get("sections") or {})
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_174)
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_170)
    assert board["composes_upstream_layers_not_duplicates"] is True
    assert board["sources"]["composes_governed_lane_entry_recommendation"] is True
    assert "lane_recommendation_upstream_read" in section_keys
    assert "authorization_envelope_status" in section_keys
    assert "lane_readiness_board_packet" in section_keys
    assert board["lane_readiness_board_not_admission_decision"] is True


def test_governed_lane_readiness_board_api_readonly():
    session = "mc-glrb-175"
    _lane_board_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governed-lane-readiness-board",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["lane_admission_decision_performed"] is False
    assert body["lane_admission_performed"] is False
    board = body["governed_lane_readiness_board"]
    assert board["schema_version"] == "mission_control_governed_lane_readiness_board_v1"
    assert "recommended_lane_candidates_board" in board["sections"]
    assert "risk_blast_radius_summary" in board["sections"]
    assert "Governed Lane Readiness Board" in body["markdown"]


def test_governed_lane_readiness_board_record_persists():
    session = "mc-glrb-record-175"
    _lane_board_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governed-lane-readiness-board/record",
        json={
            "session_id": session,
            "kind": "lane_readiness_board_artifact",
            "content": "Board ready for human lane admission review.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["governed_lane_readiness_board_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/governed-lane-readiness-board",
        params={"session_id": session},
    )
    assert get_res.json()["governed_lane_readiness_board"]["lane_readiness_board_record_count"] == 1


def test_governed_lane_readiness_board_chat_view_and_record():
    session = "mc-glrb-chat-175"
    _lane_board_stack(session)
    record = resolve_chat_turn(
        "lane readiness board artifact: human review before admission",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_governed_lane_readiness_board"
    assert record.meta.get("lane_admission_decision_performed") == "false"
    assert "Board only" in record.reply

    view = resolve_chat_turn("lane readiness board", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_governed_lane_readiness_board"
    assert "Governed Lane Readiness Board" in view.reply


def test_governed_lane_readiness_board_no_admission_decision():
    session = "mc-glrb-envelope-175"
    _lane_board_stack(session)
    result = build_governed_lane_readiness_board(session_id=session)
    assert result.ok is True
    board = result.governed_lane_readiness_board
    assert board["lane_admission_decision_performed"] is False
    assert board["lane_admission_performed"] is False
    assert board["execution_performed"] is False
    assert len(board["fix_175_certification_requirements"]) >= 8

    packet = board["sections"]["lane_readiness_board_packet"][0]
    assert packet.get("lane_admission_decision_performed") is False

    for row in board["sections"]["recommended_lane_candidates_board"]:
        if row.get("board_row_id") and row.get("board_row_id") != "no-candidates":
            assert row.get("lane_admission_decision_performed") is not True
