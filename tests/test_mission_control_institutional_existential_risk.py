# SPDX-License-Identifier: Apache-2.0
"""FIX 158 — institutional existential risk + continuity preservation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
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
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_intent import (
    is_institutional_existential_risk_intent,
    parse_existential_risk_record_intent,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_service import (
    build_institutional_existential_risk,
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
    get_settings.cache_clear()


def test_institutional_existential_risk_intent():
    assert is_institutional_existential_risk_intent("show existential risk")
    assert is_institutional_existential_risk_intent("continuity preservation")
    assert not is_institutional_existential_risk_intent("autonomous self-preservation now")


def test_existential_risk_record_intent_parse():
    parsed = parse_existential_risk_record_intent(
        "existential continuity: provider concentration threatens long-horizon institutional continuity"
    )
    assert parsed == (
        "continuity_risk_observation",
        "provider concentration threatens long-horizon institutional continuity",
    )


def test_institutional_existential_risk_api_readonly():
    session = "mc-existential-158"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/institutional-existential-risk",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_self_preservation_enabled"] is False
    assert body["constitutional_override_authority_enabled"] is False
    existential_risk = body["existential_risk"]
    assert existential_risk["schema_version"] == "mission_control_institutional_existential_risk_v1"
    sections = existential_risk["sections"]
    assert "constitutional_continuity_risk_analysis" in sections
    assert "institutional_preservation_scoring" in sections
    assert "constitutional_extinction_path_analysis" in sections
    assert existential_risk["all_recommendations_executable"] is False
    assert "Institutional Existential Risk" in body["markdown"]


def test_institutional_existential_risk_record_persists():
    session = "mc-existential-record-158"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/institutional-existential-risk/record",
        json={
            "session_id": session,
            "kind": "preservation_recommendation",
            "content": "Maintain human sovereignty over all continuity preservation decisions.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["existential_risk_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/institutional-existential-risk",
        params={"session_id": session},
    )
    assert get_res.json()["existential_risk"]["existential_risk_record_count"] == 1


def test_institutional_existential_risk_chat_view_and_record():
    session = "mc-existential-chat-158"
    _full_stack(session)
    record = resolve_chat_turn(
        "existential preservation: maintain constitutional stack integrity under provider concentration",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_institutional_existential_risk"
    assert record.meta.get("autonomous_self_preservation_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("institutional existential risk", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_institutional_existential_risk"
    assert "Institutional Existential Risk" in view.reply


def test_institutional_existential_risk_builds_from_external_relations():
    session = "mc-existential-src-158"
    _full_stack(session)
    result = build_institutional_existential_risk(session_id=session)
    assert result.ok is True
    assert result.existential_risk["sources"]["institutional_external_relations"] is True
    assert len(result.existential_risk["existential_risk_principles"]) >= 8
    assert len(result.existential_risk["sections"]["governance_collapse_scenario_modeling"]) >= 4
