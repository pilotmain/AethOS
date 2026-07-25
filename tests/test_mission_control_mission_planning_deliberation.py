# SPDX-License-Identifier: Apache-2.0
"""FIX 165 — mission planning multi-agent deliberation."""

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
from aethos_core.mission_control.mission_planning.mission_planning_store import (
    clear_mission_planning_records_for_tests,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_intent import (
    is_mission_planning_deliberation_intent,
    parse_deliberation_record_intent,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_service import (
    build_mission_planning_deliberation,
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
    get_settings.cache_clear()


def test_mission_planning_deliberation_intent():
    assert is_mission_planning_deliberation_intent("show planning deliberation")
    assert is_mission_planning_deliberation_intent("multi-agent deliberation")
    assert not is_mission_planning_deliberation_intent("autonomous execution now")


def test_deliberation_record_intent_parse():
    parsed = parse_deliberation_record_intent(
        "deliberation planner: compare hold path against governed delivery continuation"
    )
    assert parsed == (
        "planner_analysis_note",
        "compare hold path against governed delivery continuation",
    )


def test_mission_planning_deliberation_api_readonly():
    session = "mc-deliberation-165"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/mission-planning-deliberation",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_execution_enabled"] is False
    assert body["autonomous_lane_selection_enabled"] is False
    deliberation = body["mission_planning_deliberation"]
    assert deliberation["schema_version"] == "mission_control_mission_planning_deliberation_v1"
    sections = deliberation["sections"]
    assert "planner_agent_analysis" in sections
    assert "consolidated_recommendation" in sections
    assert deliberation["agent_role_count"] == 6
    assert deliberation["all_recommendations_executable"] is False
    assert "Multi-Agent Deliberation" in body["markdown"]


def test_mission_planning_deliberation_record_persists():
    session = "mc-deliberation-record-165"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/mission-planning-deliberation/record",
        json={
            "session_id": session,
            "kind": "planner_analysis_note",
            "content": "PlannerAgent notes hold path until constitutional tradeoffs are human-reviewed.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["mission_planning_deliberation_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/mission-planning-deliberation",
        params={"session_id": session},
    )
    assert get_res.json()["mission_planning_deliberation"]["deliberation_record_count"] == 1


def test_mission_planning_deliberation_chat_view_and_record():
    session = "mc-deliberation-chat-165"
    _full_stack(session)
    record = resolve_chat_turn(
        "deliberation synthesis: bounded agents completed analysis without autonomous path selection",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_mission_planning_deliberation"
    assert record.meta.get("autonomous_execution_enabled") == "false"
    assert "Analysis-only" in record.reply

    view = resolve_chat_turn("planning deliberation", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_mission_planning_deliberation"
    assert "Multi-Agent Deliberation" in view.reply


def test_mission_planning_deliberation_builds_from_mission_planning():
    session = "mc-deliberation-src-165"
    _full_stack(session)
    result = build_mission_planning_deliberation(session_id=session)
    assert result.ok is True
    assert result.mission_planning_deliberation["sources"]["mission_planning"] is True
    assert len(result.mission_planning_deliberation["deliberation_principles"]) >= 8
    assert len(result.mission_planning_deliberation["agent_outputs"]) == 6
    role_ids = [o.get("agent_role_id") for o in result.mission_planning_deliberation["agent_outputs"]]
    assert "planner_agent" in role_ids
    assert "synthesis_agent" in role_ids
