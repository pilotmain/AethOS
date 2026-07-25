# SPDX-License-Identifier: Apache-2.0
"""FIX 173 — gate-routed package outcome review."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
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
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_intent import (
    is_gate_routed_package_outcome_review_intent,
    parse_gate_routed_package_outcome_review_record_intent,
)
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_service import (
    build_gate_routed_package_outcome_review,
)
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
    clear_gate_routed_package_outcome_review_records_for_tests,
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
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
    append_governed_task_execution_coordination_record,
    clear_governed_task_execution_coordination_records_for_tests,
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
    clear_governed_task_execution_coordination_records_for_tests()
    clear_gate_routed_package_outcome_review_records_for_tests()
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
    clear_governed_task_execution_coordination_records_for_tests()
    clear_gate_routed_package_outcome_review_records_for_tests()
    get_settings.cache_clear()


def _gate_review_stack(session: str) -> None:
    _full_stack(session)
    append_human_decision_board_record(
        session_id=session,
        kind="selection_record",
        content="governed_delivery_continuation",
    )
    append_execution_handoff_coordination_record(
        session_id=session,
        kind="handoff_artifact",
        content="Handoff for gate-routed package outcome review.",
    )
    append_bounded_delivery_work_packages_record(
        session_id=session,
        kind="work_package_artifact",
        content="Work packages for outcome review.",
    )
    append_mission_authorization_record(
        session_id=session,
        kind="mission_authorization_artifact",
        content="Bounded Tier 1-2 envelope for gate review.",
    )
    append_bounded_execution_participation_record(
        session_id=session,
        kind="participation_artifact",
        content="Agent participation within authorized envelope.",
    )
    append_governed_task_execution_coordination_record(
        session_id=session,
        kind="coordination_artifact",
        content="Coordinate packages before gate review.",
    )


def test_gate_routed_package_outcome_review_intent():
    assert is_gate_routed_package_outcome_review_intent("show gate review")
    assert is_gate_routed_package_outcome_review_intent("gate-routed package outcome review")
    assert not is_gate_routed_package_outcome_review_intent("execute now")


def test_gate_routed_package_outcome_review_record_intent_parse():
    parsed = parse_gate_routed_package_outcome_review_record_intent(
        "gate review artifact: outcomes ready for workspace_verification gate"
    )
    assert parsed == (
        "gate_review_artifact",
        "outcomes ready for workspace_verification gate",
    )


def test_gate_routed_package_outcome_review_api_readonly():
    session = "mc-gtrev-173"
    _gate_review_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/gate-routed-package-outcome-review",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["execution_performed"] is False
    assert body["gate_bypass_enabled"] is False
    assert body["code_write_enabled"] is False
    assert body["merge_deploy_enabled"] is False
    review = body["gate_routed_package_outcome_review"]
    assert review["schema_version"] == "mission_control_gate_routed_package_outcome_review_v1"
    sections = review["sections"]
    assert "package_outcome_collection" in sections
    assert "outcome_quality_classification" in sections
    assert "frozen_gate_mapping" in sections
    assert "gate_review_packet" in sections
    assert "gate_handler_routing" in sections
    assert review["review_ready"] is True
    assert review["all_recommendations_executable"] is False
    assert "Gate-Routed Package Outcome Review" in body["markdown"]


def test_gate_routed_package_outcome_review_record_persists():
    session = "mc-gtrev-record-173"
    _gate_review_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/gate-routed-package-outcome-review/record",
        json={
            "session_id": session,
            "kind": "gate_review_artifact",
            "content": "Outcomes classified — route to workspace_verification gate.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["gate_routed_package_outcome_review_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/gate-routed-package-outcome-review",
        params={"session_id": session},
    )
    assert get_res.json()["gate_routed_package_outcome_review"]["gate_review_record_count"] == 1


def test_gate_routed_package_outcome_review_chat_view_and_record():
    session = "mc-gtrev-chat-173"
    _gate_review_stack(session)
    record = resolve_chat_turn(
        "gate review artifact: classify outcomes and map to frozen gates",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_gate_routed_package_outcome_review"
    assert record.meta.get("execution_performed") == "false"
    assert "Review only" in record.reply

    view = resolve_chat_turn("show gate review", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_gate_routed_package_outcome_review"
    assert "Gate-Routed Package Outcome Review" in view.reply


def test_gate_routed_package_outcome_review_no_execution_authority():
    session = "mc-gtrev-envelope-173"
    _gate_review_stack(session)
    result = build_gate_routed_package_outcome_review(session_id=session)
    assert result.ok is True
    review = result.gate_routed_package_outcome_review
    assert review["execution_performed"] is False
    assert review["review_not_execution_authority"] is True
    assert review["autonomous_lane_entry_enabled"] is False
    assert review["gate_bypass_enabled"] is False
    assert len(review["fix_173_certification_requirements"]) >= 8

    for row in review["sections"]["frozen_gate_mapping"]:
        assert row.get("gate_bypass") is not True

    for row in review["sections"]["gate_handler_routing"]:
        assert row.get("gate_bypass") is not True
        assert row.get("execution_performed") is not True

    packet = review["sections"]["gate_review_packet"][0]
    assert packet.get("execution_performed") is False
    assert packet.get("approval_bypass") is False
    assert packet.get("gate_bypass") is False
