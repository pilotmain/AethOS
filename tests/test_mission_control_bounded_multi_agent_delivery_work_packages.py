# SPDX-License-Identifier: Apache-2.0
"""FIX 168 — bounded multi-agent delivery work packages."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_intent import (
    is_bounded_delivery_work_packages_intent,
    parse_work_packages_record_intent,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_service import (
    build_bounded_delivery_work_packages,
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
    clear_bounded_delivery_work_packages_records_for_tests()
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
    get_settings.cache_clear()


def _handoff_stack(session: str) -> None:
    _full_stack(session)
    append_human_decision_board_record(
        session_id=session,
        kind="selection_record",
        content="governed_delivery_continuation",
    )
    append_execution_handoff_coordination_record(
        session_id=session,
        kind="handoff_artifact",
        content="Handoff package for governed software delivery lane with human approval at each gate.",
    )


def test_bounded_delivery_work_packages_intent():
    assert is_bounded_delivery_work_packages_intent("show work packages")
    assert is_bounded_delivery_work_packages_intent("delivery work packages")
    assert not is_bounded_delivery_work_packages_intent("write code now")


def test_work_packages_record_intent_parse():
    parsed = parse_work_packages_record_intent(
        "work package artifact: planner scope for issue intake through workspace verification"
    )
    assert parsed == (
        "work_package_artifact",
        "planner scope for issue intake through workspace verification",
    )


def test_bounded_delivery_work_packages_api_readonly():
    session = "mc-wpkg-168"
    _handoff_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/bounded-delivery-work-packages",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_execution_enabled"] is False
    assert body["code_write_enabled"] is False
    packages = body["bounded_delivery_work_packages"]
    assert packages["schema_version"] == "mission_control_bounded_delivery_work_packages_v1"
    sections = packages["sections"]
    assert "handoff_artifact_read" in sections
    assert "role_scoped_work_packages" in sections
    assert "agent_package_assignments" in sections
    assert packages["agent_package_count"] == 5
    assert packages["selected_path_id"] == "governed_delivery_continuation"
    assert packages["all_recommendations_executable"] is False
    assert "Work Packages" in body["markdown"]


def test_bounded_delivery_work_packages_record_persists():
    session = "mc-wpkg-record-168"
    _handoff_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/bounded-delivery-work-packages/record",
        json={
            "session_id": session,
            "kind": "work_package_artifact",
            "content": "Scoped delivery packages for Planner and Verification agents pending human review.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["bounded_delivery_work_packages_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/bounded-delivery-work-packages",
        params={"session_id": session},
    )
    assert get_res.json()["bounded_delivery_work_packages"]["work_package_record_count"] == 1


def test_bounded_delivery_work_packages_chat_view_and_record():
    session = "mc-wpkg-chat-168"
    _handoff_stack(session)
    record = resolve_chat_turn(
        "work package planner: scope issue intake and implementation plan stages only",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_bounded_multi_agent_delivery_work_packages"
    assert record.meta.get("autonomous_execution_enabled") == "false"
    assert "Package scoping only" in record.reply

    view = resolve_chat_turn("delivery work packages", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_bounded_multi_agent_delivery_work_packages"
    assert "Work Packages" in view.reply


def test_bounded_delivery_work_packages_builds_from_handoff():
    session = "mc-wpkg-src-168"
    _handoff_stack(session)
    result = build_bounded_delivery_work_packages(session_id=session)
    assert result.ok is True
    assert result.bounded_delivery_work_packages["sources"]["execution_handoff_coordination"] is True
    assert result.bounded_delivery_work_packages["bounded_multi_agent_delivery"] is True
    assert len(result.bounded_delivery_work_packages["work_packages_principles"]) >= 8
    roles = {
        row.get("agent_role_id")
        for row in result.bounded_delivery_work_packages["sections"]["role_scoped_work_packages"]
        if row.get("agent_role_id")
    }
    assert "planner_agent" in roles
    assert "diff_audit_agent" in roles
    assert len(result.bounded_delivery_work_packages["sections"]["package_forbidden_actions"]) >= 4
