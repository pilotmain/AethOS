# SPDX-License-Identifier: Apache-2.0
"""FIX 161 — constitutional legitimacy + institutional trust."""

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
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_intent import (
    is_constitutional_legitimacy_intent,
    parse_legitimacy_record_intent,
)
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_service import (
    build_constitutional_legitimacy,
)
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_store import (
    clear_constitutional_legitimacy_records_for_tests,
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
    get_settings.cache_clear()


def test_constitutional_legitimacy_intent():
    assert is_constitutional_legitimacy_intent("show constitutional legitimacy")
    assert is_constitutional_legitimacy_intent("institutional trust")
    assert not is_constitutional_legitimacy_intent("public trust manipulation now")


def test_legitimacy_record_intent_parse():
    parsed = parse_legitimacy_record_intent(
        "legitimacy confidence: operator trust in chat-governed governance remains strong"
    )
    assert parsed == (
        "stakeholder_confidence_note",
        "operator trust in chat-governed governance remains strong",
    )


def test_constitutional_legitimacy_api_readonly():
    session = "mc-legitimacy-161"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/constitutional-legitimacy",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_legitimacy_enforcement_enabled"] is False
    assert body["public_trust_manipulation_enabled"] is False
    constitutional_legitimacy = body["constitutional_legitimacy"]
    assert constitutional_legitimacy["schema_version"] == "mission_control_constitutional_legitimacy_v1"
    sections = constitutional_legitimacy["sections"]
    assert "institutional_trust_continuity_analysis" in sections
    assert "institutional_confidence_scoring" in sections
    assert "institutional_credibility_reconstruction" in sections
    assert constitutional_legitimacy["all_recommendations_executable"] is False
    assert "Constitutional Legitimacy" in body["markdown"]


def test_constitutional_legitimacy_record_persists():
    session = "mc-legitimacy-record-161"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/constitutional-legitimacy/record",
        json={
            "session_id": session,
            "kind": "legitimacy_tracking_record",
            "content": "Human operators govern all legitimacy and trust continuity decisions.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["constitutional_legitimacy_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/constitutional-legitimacy",
        params={"session_id": session},
    )
    assert get_res.json()["constitutional_legitimacy"]["legitimacy_record_count"] == 1


def test_constitutional_legitimacy_chat_view_and_record():
    session = "mc-legitimacy-chat-161"
    _full_stack(session)
    record = resolve_chat_turn(
        "legitimacy trust: institutional trust continuity under bounded constitutional cognition",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_constitutional_legitimacy"
    assert record.meta.get("autonomous_legitimacy_enforcement_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("constitutional legitimacy", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_constitutional_legitimacy"
    assert "Constitutional Legitimacy" in view.reply


def test_constitutional_legitimacy_builds_from_audit():
    session = "mc-legitimacy-src-161"
    _full_stack(session)
    result = build_constitutional_legitimacy(session_id=session)
    assert result.ok is True
    assert result.constitutional_legitimacy["sources"]["constitutional_audit"] is True
    assert len(result.constitutional_legitimacy["legitimacy_principles"]) >= 8
    assert len(result.constitutional_legitimacy["sections"]["governance_legitimacy_indicators"]) >= 4
