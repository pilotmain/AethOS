# SPDX-License-Identifier: Apache-2.0
"""FIX 167 — governed execution handoff coordination."""

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
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_intent import (
    is_execution_handoff_coordination_intent,
    parse_handoff_record_intent,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_service import (
    build_execution_handoff_coordination,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_store import (
    append_execution_handoff_coordination_record,
    clear_execution_handoff_coordination_records_for_tests,
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
from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
    append_human_decision_board_record,
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
    clear_execution_handoff_coordination_records_for_tests()
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
    clear_execution_handoff_coordination_records_for_tests()
    get_settings.cache_clear()


def test_execution_handoff_coordination_intent():
    assert is_execution_handoff_coordination_intent("show execution handoff")
    assert is_execution_handoff_coordination_intent("handoff package")
    assert not is_execution_handoff_coordination_intent("autonomous execution now")


def test_handoff_record_intent_parse():
    parsed = parse_handoff_record_intent(
        "handoff artifact: governed delivery handoff to software_delivery lane pending human approval"
    )
    assert parsed == (
        "handoff_artifact",
        "governed delivery handoff to software_delivery lane pending human approval",
    )


def test_execution_handoff_coordination_api_readonly():
    session = "mc-handoff-167"
    _full_stack(session)
    append_human_decision_board_record(
        session_id=session,
        kind="selection_record",
        content="governed_delivery_continuation with explicit human approval at each gate",
    )
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/execution-handoff-coordination",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_execution_enabled"] is False
    assert body["autonomous_lane_entry_enabled"] is False
    handoff = body["execution_handoff_coordination"]
    assert handoff["schema_version"] == "mission_control_execution_handoff_coordination_v1"
    sections = handoff["sections"]
    assert "selected_human_decision_read" in sections
    assert "execution_handoff_package" in sections
    assert "next_step_command_sequence" in sections
    assert handoff["selected_path_id"] == "governed_delivery_continuation"
    assert handoff["all_recommendations_executable"] is False
    assert "Handoff Coordination" in body["markdown"]


def test_execution_handoff_coordination_record_persists():
    session = "mc-handoff-record-167"
    _full_stack(session)
    append_human_decision_board_record(
        session_id=session,
        kind="selection_record",
        content="governed_delivery_continuation",
    )
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/execution-handoff-coordination/record",
        json={
            "session_id": session,
            "kind": "handoff_artifact",
            "content": "Handoff package prepared for software_delivery lane entry with human approval.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["execution_handoff_coordination_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/execution-handoff-coordination",
        params={"session_id": session},
    )
    assert get_res.json()["execution_handoff_coordination"]["handoff_record_count"] == 1


def test_execution_handoff_coordination_chat_view_and_record():
    session = "mc-handoff-chat-167"
    _full_stack(session)
    append_human_decision_board_record(
        session_id=session,
        kind="selection_record",
        content="governed_delivery_continuation",
    )
    record = resolve_chat_turn(
        "handoff step: review software delivery loop status before lane entry",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_execution_handoff_coordination"
    assert record.meta.get("autonomous_execution_enabled") == "false"
    assert "Handoff coordination only" in record.reply

    view = resolve_chat_turn("execution handoff", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_execution_handoff_coordination"
    assert "Handoff Coordination" in view.reply


def test_execution_handoff_coordination_builds_from_human_decision():
    session = "mc-handoff-src-167"
    _full_stack(session)
    append_human_decision_board_record(
        session_id=session,
        kind="selection_record",
        content="governed_delivery_continuation",
    )
    result = build_execution_handoff_coordination(session_id=session)
    assert result.ok is True
    assert result.execution_handoff_coordination["sources"]["human_decision_board"] is True
    assert result.execution_handoff_coordination["sources"]["human_selection_recorded"] is True
    assert len(result.execution_handoff_coordination["handoff_principles"]) >= 8
    assert "software_delivery" in result.execution_handoff_coordination["sections"]["eligible_lane_mapping"][0].get(
        "eligible_lanes", []
    )
    assert len(result.execution_handoff_coordination["sections"]["forbidden_actions"]) >= 4
