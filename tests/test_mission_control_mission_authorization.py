# SPDX-License-Identifier: Apache-2.0
"""FIX 170 — mission authorization."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
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
from aethos_core.mission_control.mission_authorization.mission_authorization_intent import (
    is_mission_authorization_intent,
    parse_mission_authorization_record_intent,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_service import build_mission_authorization
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
    get_settings.cache_clear()


def _authorization_stack(session: str) -> None:
    _full_stack(session)
    append_human_decision_board_record(
        session_id=session,
        kind="selection_record",
        content="governed_delivery_continuation",
    )
    append_execution_handoff_coordination_record(
        session_id=session,
        kind="handoff_artifact",
        content="Handoff for bounded delivery mission authorization.",
    )
    append_bounded_delivery_work_packages_record(
        session_id=session,
        kind="work_package_artifact",
        content="Work packages for mission authorization envelope.",
    )


def test_mission_authorization_intent():
    assert is_mission_authorization_intent("show mission authorization")
    assert is_mission_authorization_intent("bounded work envelope")
    assert not is_mission_authorization_intent("bypass gates now")


def test_mission_authorization_record_intent_parse():
    parsed = parse_mission_authorization_record_intent(
        "mission authorization: bounded Tier 1-2 envelope for software_delivery only"
    )
    assert parsed == (
        "mission_authorization_artifact",
        "bounded Tier 1-2 envelope for software_delivery only",
    )


def test_mission_authorization_api_readonly():
    session = "mc-mauth-170"
    _authorization_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/mission-authorization",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["gate_bypass_enabled"] is False
    assert body["tier_escalation_enabled"] is False
    auth = body["mission_authorization"]
    assert auth["schema_version"] == "mission_control_mission_authorization_v1"
    sections = auth["sections"]
    assert "bounded_work_envelope" in sections
    assert "existing_gate_checks" in sections
    assert "tier_boundary_enforcement" in sections
    assert auth["selected_path_id"] == "governed_delivery_continuation"
    assert "railway_orchestration" not in (
        sections["bounded_work_envelope"][-1].get("allowed_lanes") or []
    )
    assert auth["all_recommendations_executable"] is False
    assert "Mission Authorization" in body["markdown"]


def test_mission_authorization_record_persists():
    session = "mc-mauth-record-170"
    _authorization_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/mission-authorization/record",
        json={
            "session_id": session,
            "kind": "mission_authorization_artifact",
            "content": "Bounded Tier 1-2 envelope for governed delivery session.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["mission_authorization_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/mission-authorization",
        params={"session_id": session},
    )
    assert get_res.json()["mission_authorization"]["authorization_record_count"] == 1


def test_mission_authorization_chat_view_and_record():
    session = "mc-mauth-chat-170"
    _authorization_stack(session)
    record = resolve_chat_turn(
        "mission authorization: bounded envelope for software_delivery with existing gates enforced",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_mission_authorization"
    assert record.meta.get("gate_bypass_enabled") == "false"
    assert "Bounded envelope only" in record.reply

    view = resolve_chat_turn("mission authorization", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_mission_authorization"
    assert "Mission Authorization" in view.reply


def test_mission_authorization_envelope_no_railway_production():
    session = "mc-mauth-envelope-170"
    _authorization_stack(session)
    result = build_mission_authorization(session_id=session)
    assert result.ok is True
    envelope = result.mission_authorization["sections"]["bounded_work_envelope"][-1]
    allowed = set(envelope.get("allowed_lanes") or [])
    forbidden = set(envelope.get("forbidden_implicit_lanes") or [])
    assert "software_delivery" in allowed
    assert not allowed.intersection({"railway_orchestration", "production_governance"})
    assert forbidden >= {"railway_orchestration", "production_governance"}
    assert envelope.get("gate_bypass") is False
    assert result.mission_authorization["gate_bypass_enabled"] is False
    assert len(result.mission_authorization["fix_170_certification_requirements"]) >= 7
