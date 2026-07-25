# SPDX-License-Identifier: Apache-2.0
"""FIX 157 — institutional external relations + constitutional boundary."""

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
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_intent import (
    is_institutional_external_relations_intent,
    parse_external_relations_record_intent,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_service import (
    build_institutional_external_relations,
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
    get_settings.cache_clear()


def test_institutional_external_relations_intent():
    assert is_institutional_external_relations_intent("show external relations")
    assert is_institutional_external_relations_intent("constitutional boundary")
    assert not is_institutional_external_relations_intent("autonomous external negotiation now")


def test_external_relations_record_intent_parse():
    parsed = parse_external_relations_record_intent(
        "external provider: github software delivery lane under chat-governed approval boundary"
    )
    assert parsed == (
        "provider_relationship",
        "github software delivery lane under chat-governed approval boundary",
    )


def test_institutional_external_relations_api_readonly():
    session = "mc-external-157"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/institutional-external-relations",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_external_negotiation_enabled"] is False
    assert body["sovereignty_delegation_enabled"] is False
    external_relations = body["external_relations"]
    assert external_relations["schema_version"] == "mission_control_institutional_external_relations_v1"
    sections = external_relations["sections"]
    assert "external_provider_relationship_models" in sections
    assert "constitutional_boundary_definitions" in sections
    assert "cross_system_trust_continuity" in sections
    assert external_relations["all_recommendations_executable"] is False
    assert "Institutional External Relations" in body["markdown"]


def test_institutional_external_relations_record_persists():
    session = "mc-external-record-157"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/institutional-external-relations/record",
        json={
            "session_id": session,
            "kind": "boundary_definition",
            "content": "Provider mutation boundary: all external actions via chat-governed lanes only.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["external_relations_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/institutional-external-relations",
        params={"session_id": session},
    )
    assert get_res.json()["external_relations"]["external_relations_record_count"] == 1


def test_institutional_external_relations_chat_view_and_record():
    session = "mc-external-chat-157"
    _full_stack(session)
    record = resolve_chat_turn(
        "external trust: github classified as governed_provider under constitutional boundary",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_institutional_external_relations"
    assert record.meta.get("autonomous_external_negotiation_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("institutional external relations", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_institutional_external_relations"
    assert "Institutional External Relations" in view.reply


def test_institutional_external_relations_builds_from_identity():
    session = "mc-external-src-157"
    _full_stack(session)
    result = build_institutional_external_relations(session_id=session)
    assert result.ok is True
    assert result.external_relations["sources"]["institutional_identity"] is True
    assert len(result.external_relations["external_relations_principles"]) >= 8
    assert len(result.external_relations["sections"]["external_provider_relationship_models"]) >= 4
