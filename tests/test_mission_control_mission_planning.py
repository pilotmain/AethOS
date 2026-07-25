# SPDX-License-Identifier: Apache-2.0
"""FIX 164 — mission planning + institutional action cognition."""

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
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_store import (
    clear_institutional_existential_risk_records_for_tests,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_store import (
    clear_institutional_external_relations_records_for_tests,
)
from aethos_core.mission_control.institutional_identity.institutional_identity_store import (
    clear_institutional_identity_records_for_tests,
)
from aethos_core.mission_control.mission_planning.mission_planning_intent import (
    is_mission_planning_intent,
    parse_planning_record_intent,
)
from aethos_core.mission_control.mission_planning.mission_planning_service import build_mission_planning
from aethos_core.mission_control.mission_planning.mission_planning_store import (
    clear_mission_planning_records_for_tests,
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
    get_settings.cache_clear()


def test_mission_planning_intent():
    assert is_mission_planning_intent("show mission planning")
    assert is_mission_planning_intent("institutional action options")
    assert not is_mission_planning_intent("execute action autonomously now")


def test_planning_record_intent_parse():
    parsed = parse_planning_record_intent(
        "planning option: continue governed software delivery with explicit human approval at each gate"
    )
    assert parsed == (
        "action_option_note",
        "continue governed software delivery with explicit human approval at each gate",
    )


def test_mission_planning_api_readonly():
    session = "mc-planning-164"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/mission-planning",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_action_execution_enabled"] is False
    assert body["auto_path_selection_enabled"] is False
    mission_planning = body["mission_planning"]
    assert mission_planning["schema_version"] == "mission_control_mission_planning_v1"
    sections = mission_planning["sections"]
    assert "action_option_generation" in sections
    assert "lane_touch_mapping" in sections
    assert "mission_action_plan_artifact" in sections
    assert mission_planning["all_recommendations_executable"] is False
    assert "Mission Planning" in body["markdown"]


def test_mission_planning_record_persists():
    session = "mc-planning-record-164"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/mission-planning/record",
        json={
            "session_id": session,
            "kind": "action_option_note",
            "content": "Consider governed software delivery continuation with human approval gates.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["mission_planning_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/mission-planning",
        params={"session_id": session},
    )
    assert get_res.json()["mission_planning"]["planning_record_count"] == 1


def test_mission_planning_chat_view_and_record():
    session = "mc-planning-chat-164"
    _full_stack(session)
    record = resolve_chat_turn(
        "planning option: hold institutional action until constitutional tradeoffs are human-reviewed",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_mission_planning"
    assert record.meta.get("autonomous_action_execution_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("mission planning", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_mission_planning"
    assert "Mission Planning" in view.reply


def test_mission_planning_builds_from_synthesis_and_orchestration():
    session = "mc-planning-src-164"
    _full_stack(session)
    result = build_mission_planning(session_id=session)
    assert result.ok is True
    assert result.mission_planning["sources"]["constitutional_synthesis"] is True
    assert result.mission_planning["sources"]["mission_orchestration"] is True
    assert len(result.mission_planning["planning_principles"]) >= 8
    assert len(result.mission_planning["sections"]["action_option_generation"]) >= 4
    assert len(result.mission_planning["sections"]["do_not_do_paths"]) >= 4
