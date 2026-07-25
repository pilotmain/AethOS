# SPDX-License-Identifier: Apache-2.0
"""FIX 156 — institutional identity + constitutional intent."""

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
from aethos_core.mission_control.institutional_identity.institutional_identity_intent import (
    is_institutional_identity_intent,
    parse_identity_record_intent,
)
from aethos_core.mission_control.institutional_identity.institutional_identity_service import (
    build_institutional_identity,
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
    get_settings.cache_clear()


def test_institutional_identity_intent():
    assert is_institutional_identity_intent("show institutional identity")
    assert is_institutional_identity_intent("constitutional intent")
    assert not is_institutional_identity_intent("autonomous institutional redirection now")


def test_identity_record_intent_parse():
    parsed = parse_identity_record_intent(
        "identity mission: governed operational intelligence without autonomous execution authority"
    )
    assert parsed == (
        "mission_identity",
        "governed operational intelligence without autonomous execution authority",
    )


def test_institutional_identity_api_readonly():
    session = "mc-identity-156"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/institutional-identity",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_institutional_redirection_enabled"] is False
    assert body["automatic_constitutional_rewriting_enabled"] is False
    assert body["governance_sovereignty_delegated"] is False
    identity = body["identity"]
    assert identity["schema_version"] == "mission_control_institutional_identity_v1"
    sections = identity["sections"]
    assert "institutional_mission_identity_records" in sections
    assert "constitutional_intent_lineage" in sections
    assert "institutional_narrative_continuity" in sections
    assert identity["all_recommendations_executable"] is False
    assert "Institutional Identity" in body["markdown"]


def test_institutional_identity_record_persists():
    session = "mc-identity-record-156"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/institutional-identity/record",
        json={
            "session_id": session,
            "kind": "constitutional_intent",
            "content": "Enduring intent: constitutional cognition without governance sovereignty.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["identity_memory_only"] is True

    get_res = client.get("/api/v1/mission-control/institutional-identity", params={"session_id": session})
    assert get_res.json()["identity"]["identity_record_count"] == 1


def test_institutional_identity_chat_view_and_record():
    session = "mc-identity-chat-156"
    _full_stack(session)
    record = resolve_chat_turn(
        "identity intent: human governance sovereignty remains primary across all constitutional layers",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_institutional_identity"
    assert record.meta.get("autonomous_institutional_redirection_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("institutional identity", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_institutional_identity"
    assert "Institutional Identity" in view.reply


def test_institutional_identity_builds_from_evolution():
    session = "mc-identity-src-156"
    _full_stack(session)
    result = build_institutional_identity(session_id=session)
    assert result.ok is True
    assert result.identity["sources"]["governance_evolution"] is True
    assert len(result.identity["identity_cognition_principles"]) >= 8
    assert len(result.identity["sections"]["institutional_mission_identity_records"]) >= 5
