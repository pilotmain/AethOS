# SPDX-License-Identifier: Apache-2.0
"""FIX 169 — work package readiness + lane admission."""

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
from aethos_core.mission_control.mission_planning.mission_planning_store import (
    clear_mission_planning_records_for_tests,
)
from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_store import (
    clear_mission_planning_deliberation_records_for_tests,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_intent import (
    is_work_package_readiness_lane_admission_intent,
    parse_lane_admission_record_intent,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_service import (
    build_work_package_readiness_lane_admission,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_store import (
    append_work_package_readiness_lane_admission_record,
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
    get_settings.cache_clear()


def _admission_stack(session: str) -> None:
    _full_stack(session)
    append_human_decision_board_record(
        session_id=session,
        kind="selection_record",
        content="governed_delivery_continuation",
    )
    append_execution_handoff_coordination_record(
        session_id=session,
        kind="handoff_artifact",
        content="Handoff package for governed software delivery lane.",
    )
    append_bounded_delivery_work_packages_record(
        session_id=session,
        kind="work_package_artifact",
        content="Scoped delivery packages for all bounded agents.",
    )


def test_work_package_readiness_lane_admission_intent():
    assert is_work_package_readiness_lane_admission_intent("show lane admission")
    assert is_work_package_readiness_lane_admission_intent("work package readiness")
    assert not is_work_package_readiness_lane_admission_intent("autonomous lane entry now")


def test_lane_admission_record_intent_parse():
    parsed = parse_lane_admission_record_intent(
        "admission artifact: planner package ready for software_delivery lane pending human authorization"
    )
    assert parsed == (
        "lane_admission_artifact",
        "planner package ready for software_delivery lane pending human authorization",
    )


def test_work_package_readiness_lane_admission_api_readonly():
    session = "mc-adm-169"
    _admission_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/work-package-readiness-lane-admission",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_lane_entry_enabled"] is False
    assert body["code_write_enabled"] is False
    admission = body["work_package_readiness_lane_admission"]
    assert admission["schema_version"] == "mission_control_work_package_readiness_lane_admission_v1"
    sections = admission["sections"]
    assert "package_readiness_checks" in sections
    assert "lane_admission_analysis" in sections
    assert "lane_admission_package" in sections
    assert admission["agent_package_count"] == 5
    assert admission["all_recommendations_executable"] is False
    assert "Lane Admission" in body["markdown"]


def test_work_package_readiness_lane_admission_record_persists():
    session = "mc-adm-record-169"
    _admission_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/work-package-readiness-lane-admission/record",
        json={
            "session_id": session,
            "kind": "lane_admission_artifact",
            "content": "Lane admission package for software_delivery pending human authorization.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["work_package_readiness_lane_admission_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/work-package-readiness-lane-admission",
        params={"session_id": session},
    )
    assert get_res.json()["work_package_readiness_lane_admission"]["lane_admission_record_count"] == 1


def test_work_package_readiness_lane_admission_chat_view_and_record():
    session = "mc-adm-chat-169"
    _admission_stack(session)
    record = resolve_chat_turn(
        "admission readiness: planner package inputs complete pending gate review",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_work_package_readiness_lane_admission"
    assert record.meta.get("autonomous_lane_entry_enabled") == "false"
    assert "Readiness evaluation only" in record.reply

    view = resolve_chat_turn("lane admission", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_work_package_readiness_lane_admission"
    assert "Lane Admission" in view.reply


def test_work_package_readiness_lane_admission_builds_from_work_packages():
    session = "mc-adm-src-169"
    _admission_stack(session)
    result = build_work_package_readiness_lane_admission(session_id=session)
    assert result.ok is True
    assert result.work_package_readiness_lane_admission["sources"]["bounded_delivery_work_packages"] is True
    assert result.work_package_readiness_lane_admission["work_package_readiness_lane_admission_cognition"] is True
    assert len(result.work_package_readiness_lane_admission["lane_admission_principles"]) >= 8
    checks = result.work_package_readiness_lane_admission["sections"]["package_readiness_checks"]
    check_ids = {c.get("check_id") for c in checks}
    assert "inputs-complete" in check_ids
    assert "gates-satisfied" in check_ids
    assert len(result.work_package_readiness_lane_admission["sections"]["admission_forbidden_actions"]) >= 4
