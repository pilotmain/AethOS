# SPDX-License-Identifier: Apache-2.0
"""FIX 166 — human decision board + action selection."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.constitutional_audit.constitutional_audit_store import (
    clear_constitutional_audit_records_for_tests,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_store import (
    clear_constitutional_ethics_records_for_tests,
)
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_store import (
    clear_constitutional_legitimacy_records_for_tests,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_store import (
    clear_constitutional_pluralism_records_for_tests,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_store import (
    clear_constitutional_synthesis_records_for_tests,
)
from aethos_core.mission_control.governance_coherence.governance_coherence_store import (
    clear_governance_coherence_records_for_tests,
)
from aethos_core.mission_control.governance_collaboration.governance_collaboration_store import (
    clear_governance_collaboration_records_for_tests,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_store import (
    clear_governance_deliberation_records_for_tests,
)
from aethos_core.mission_control.governance_doctrine.governance_doctrine_store import (
    clear_governance_doctrine_records_for_tests,
)
from aethos_core.mission_control.governance_evolution.governance_evolution_store import (
    clear_governance_evolution_records_for_tests,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_store import (
    clear_governance_policy_interpretation_records_for_tests,
)
from aethos_core.mission_control.governance_resilience.governance_resilience_store import (
    clear_governance_resilience_records_for_tests,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_intent import (
    is_human_decision_board_intent,
    parse_decision_record_intent,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_service import (
    build_human_decision_board,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
    clear_human_decision_board_records_for_tests,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_store import (
    clear_institutional_existential_risk_records_for_tests,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_store import (
    clear_institutional_external_relations_records_for_tests,
)
from aethos_core.mission_control.institutional_identity.institutional_identity_store import (
    clear_institutional_identity_records_for_tests,
)
from aethos_core.mission_control.mission_planning.mission_planning_store import (
    clear_mission_planning_records_for_tests,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_store import (
    clear_mission_planning_deliberation_records_for_tests,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.approval_inbox.approval_execution_service import clear_ui_approval_audit_for_tests
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_deliberation_records_for_tests()
    clear_governance_collaboration_records_for_tests()
    clear_governance_doctrine_records_for_tests()
    clear_governance_policy_interpretation_records_for_tests()
    clear_governance_coherence_records_for_tests()
    clear_governance_resilience_records_for_tests()
    clear_governance_evolution_records_for_tests()
    clear_institutional_identity_records_for_tests()
    clear_institutional_external_relations_records_for_tests()
    clear_institutional_existential_risk_records_for_tests()
    clear_constitutional_ethics_records_for_tests()
    clear_constitutional_audit_records_for_tests()
    clear_constitutional_legitimacy_records_for_tests()
    clear_constitutional_pluralism_records_for_tests()
    clear_constitutional_synthesis_records_for_tests()
    clear_mission_planning_records_for_tests()
    clear_mission_planning_deliberation_records_for_tests()
    clear_human_decision_board_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_deliberation_records_for_tests()
    clear_governance_collaboration_records_for_tests()
    clear_governance_doctrine_records_for_tests()
    clear_governance_policy_interpretation_records_for_tests()
    clear_governance_coherence_records_for_tests()
    clear_governance_resilience_records_for_tests()
    clear_governance_evolution_records_for_tests()
    clear_institutional_identity_records_for_tests()
    clear_institutional_external_relations_records_for_tests()
    clear_institutional_existential_risk_records_for_tests()
    clear_constitutional_ethics_records_for_tests()
    clear_constitutional_audit_records_for_tests()
    clear_constitutional_legitimacy_records_for_tests()
    clear_constitutional_pluralism_records_for_tests()
    clear_constitutional_synthesis_records_for_tests()
    clear_mission_planning_records_for_tests()
    clear_mission_planning_deliberation_records_for_tests()
    clear_human_decision_board_records_for_tests()
    get_settings.cache_clear()


def test_human_decision_board_intent():
    assert is_human_decision_board_intent("show human decision board")
    assert is_human_decision_board_intent("candidate action board")
    assert not is_human_decision_board_intent("autonomous selection now")


def test_decision_record_intent_parse():
    parsed = parse_decision_record_intent(
        "decision select: governed_delivery_continuation with explicit human approval at each gate"
    )
    assert parsed == (
        "selection_record",
        "governed_delivery_continuation with explicit human approval at each gate",
    )


def test_human_decision_board_api_readonly():
    session = "mc-decision-166"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/human-decision-board",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_selection_enabled"] is False
    assert body["autonomous_execution_enabled"] is False
    board = body["human_decision_board"]
    assert board["schema_version"] == "mission_control_human_decision_board_v1"
    sections = board["sections"]
    assert "candidate_action_board" in sections
    assert "human_selection_record" in sections
    assert "decision_review_package" in sections
    assert board["candidate_count"] >= 4
    assert board["all_recommendations_executable"] is False
    assert "Human Decision Board" in body["markdown"]


def test_human_decision_board_record_persists():
    session = "mc-decision-record-166"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/human-decision-board/record",
        json={
            "session_id": session,
            "kind": "selection_record",
            "content": "hold_no_go_path until constitutional tradeoffs are human-reviewed",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["human_decision_board_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/human-decision-board",
        params={"session_id": session},
    )
    board = get_res.json()["human_decision_board"]
    assert board["decision_record_count"] == 1
    assert "hold_no_go_path" in board["sections"]["human_selection_record"][0].get("selected_path", "")


def test_human_decision_board_chat_view_and_record():
    session = "mc-decision-chat-166"
    _full_stack(session)
    record = resolve_chat_turn(
        "decision rationale: hold selected until multi-agent deliberation tradeoffs are consciously accepted",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_human_decision_board"
    assert record.meta.get("autonomous_selection_enabled") == "false"
    assert "Human choice only" in record.reply

    view = resolve_chat_turn("human decision board", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_human_decision_board"
    assert "Human Decision Board" in view.reply


def test_human_decision_board_builds_from_deliberation():
    session = "mc-decision-src-166"
    _full_stack(session)
    result = build_human_decision_board(session_id=session)
    assert result.ok is True
    assert result.human_decision_board["sources"]["mission_planning_deliberation"] is True
    assert len(result.human_decision_board["decision_principles"]) >= 8
    assert len(result.human_decision_board["sections"]["candidate_action_board"]) >= 4
    assert result.human_decision_board["sections"]["decision_traceability"][0]["agent_participation_count"] == 6
