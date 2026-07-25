# SPDX-License-Identifier: Apache-2.0
"""FIX 171 — bounded execution participation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_intent import (
    is_bounded_execution_participation_intent,
    parse_bounded_execution_participation_record_intent,
)
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_service import (
    build_bounded_execution_participation,
)
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_store import (
    append_bounded_execution_participation_record,
    clear_bounded_execution_participation_records_for_tests,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_store import (
    append_bounded_delivery_work_packages_record,
    clear_bounded_delivery_work_packages_records_for_tests,
)
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
from aethos_core.mission_control.mission_authorization.mission_authorization_store import (
    append_mission_authorization_record,
    clear_mission_authorization_records_for_tests,
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
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_store import (
    clear_work_package_readiness_lane_admission_records_for_tests,
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
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_work_package_readiness_lane_admission_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()
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
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_work_package_readiness_lane_admission_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()
    get_settings.cache_clear()


def _participation_stack(session: str) -> None:
    _full_stack(session)
    append_human_decision_board_record(
        session_id=session,
        kind="selection_record",
        content="governed_delivery_continuation",
    )
    append_execution_handoff_coordination_record(
        session_id=session,
        kind="handoff_artifact",
        content="Handoff for bounded execution participation.",
    )
    append_bounded_delivery_work_packages_record(
        session_id=session,
        kind="work_package_artifact",
        content="Work packages for bounded execution participation.",
    )
    append_mission_authorization_record(
        session_id=session,
        kind="mission_authorization_artifact",
        content="Bounded Tier 1-2 envelope for agent participation.",
    )


def test_bounded_execution_participation_intent():
    assert is_bounded_execution_participation_intent("show bounded execution participation")
    assert is_bounded_execution_participation_intent("agent participation")
    assert not is_bounded_execution_participation_intent("autonomous lane entry now")


def test_bounded_execution_participation_record_intent_parse():
    parsed = parse_bounded_execution_participation_record_intent(
        "participation artifact: agent scope within software_delivery envelope"
    )
    assert parsed == (
        "participation_artifact",
        "agent scope within software_delivery envelope",
    )


def test_bounded_execution_participation_api_readonly():
    session = "mc-bepart-171"
    _participation_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/bounded-execution-participation",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["autonomous_lane_entry_enabled"] is False
    assert body["gate_bypass_enabled"] is False
    assert body["merge_deploy_enabled"] is False
    participation = body["bounded_execution_participation"]
    assert participation["schema_version"] == "mission_control_bounded_execution_participation_v1"
    sections = participation["sections"]
    assert "authorization_envelope_read" in sections
    assert "participation_scope" in sections
    assert "gate_routed_participation" in sections
    assert participation["participation_ready"] is True
    assert participation["all_recommendations_executable"] is False
    assert "Bounded Execution Participation" in body["markdown"]


def test_bounded_execution_participation_record_persists():
    session = "mc-bepart-record-171"
    _participation_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/bounded-execution-participation/record",
        json={
            "session_id": session,
            "kind": "participation_artifact",
            "content": "Agent participation within authorized software_delivery envelope.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["bounded_execution_participation_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/bounded-execution-participation",
        params={"session_id": session},
    )
    assert get_res.json()["bounded_execution_participation"]["participation_record_count"] == 1


def test_bounded_execution_participation_chat_view_and_record():
    session = "mc-bepart-chat-171"
    _participation_stack(session)
    record = resolve_chat_turn(
        "participation artifact: agent scope within authorized envelope",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_bounded_execution_participation"
    assert record.meta.get("autonomous_lane_entry_enabled") == "false"
    assert "Envelope-scoped coordination only" in record.reply

    view = resolve_chat_turn("bounded execution participation", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_bounded_execution_participation"
    assert "Bounded Execution Participation" in view.reply


def test_bounded_execution_participation_envelope_scoped_no_bypass():
    session = "mc-bepart-envelope-171"
    _participation_stack(session)
    result = build_bounded_execution_participation(session_id=session)
    assert result.ok is True
    participation = result.bounded_execution_participation
    scope = participation["sections"]["participation_scope"][0 if participation["participation_record_count"] == 0 else 1]
    if scope.get("scope_id") != "envelope-participation-scope":
        scope = next(
            row for row in participation["sections"]["participation_scope"]
            if row.get("scope_id") == "envelope-participation-scope"
        )
    allowed = set(scope.get("allowed_lanes") or [])
    forbidden = set(scope.get("forbidden_lanes") or [])
    assert "software_delivery" in allowed
    assert not allowed.intersection({"railway_orchestration", "production_governance"})
    assert forbidden >= {"railway_orchestration", "production_governance"}
    assert scope.get("autonomous_lane_entry") is False
    assert participation["autonomous_lane_entry_enabled"] is False
    assert participation["gate_bypass_enabled"] is False
    assert len(participation["fix_171_certification_requirements"]) >= 8

    for row in participation["sections"]["gate_routed_participation"]:
        assert row.get("gate_bypass") is not True
        assert row.get("approval_bypass") is not True
