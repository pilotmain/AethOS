# SPDX-License-Identifier: Apache-2.0
"""FIX 162 — constitutional pluralism + governance perspective."""

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
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_intent import (
    is_constitutional_pluralism_intent,
    parse_pluralism_record_intent,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_service import (
    build_constitutional_pluralism,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_store import (
    clear_constitutional_pluralism_records_for_tests,
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
    clear_constitutional_pluralism_records_for_tests()
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
    get_settings.cache_clear()


def test_constitutional_pluralism_intent():
    assert is_constitutional_pluralism_intent("show constitutional pluralism")
    assert is_constitutional_pluralism_intent("governance perspective")
    assert not is_constitutional_pluralism_intent("authoritative worldview selection now")


def test_pluralism_record_intent_parse():
    parsed = parse_pluralism_record_intent(
        "pluralism perspective: operator governance and institutional constitutional viewpoints coexist under bounded cognition"
    )
    assert parsed == (
        "perspective_mapping_note",
        "operator governance and institutional constitutional viewpoints coexist under bounded cognition",
    )


def test_constitutional_pluralism_api_readonly():
    session = "mc-pluralism-162"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/constitutional-pluralism",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["authoritative_worldview_selection_enabled"] is False
    assert body["autonomous_constitutional_arbitration_enabled"] is False
    constitutional_pluralism = body["constitutional_pluralism"]
    assert constitutional_pluralism["schema_version"] == "mission_control_constitutional_pluralism_v1"
    sections = constitutional_pluralism["sections"]
    assert "governance_perspective_mapping" in sections
    assert "pluralistic_coherence_scoring" in sections
    assert "constitutional_disagreement_mapping" in sections
    assert constitutional_pluralism["all_recommendations_executable"] is False
    assert "Constitutional Pluralism" in body["markdown"]


def test_constitutional_pluralism_record_persists():
    session = "mc-pluralism-record-162"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/constitutional-pluralism/record",
        json={
            "session_id": session,
            "kind": "pluralism_tracking_record",
            "content": "Multiple governance perspectives tracked without authoritative worldview selection.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["constitutional_pluralism_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/constitutional-pluralism",
        params={"session_id": session},
    )
    assert get_res.json()["constitutional_pluralism"]["pluralism_record_count"] == 1


def test_constitutional_pluralism_chat_view_and_record():
    session = "mc-pluralism-chat-162"
    _full_stack(session)
    record = resolve_chat_turn(
        "pluralism disagreement: competing legitimacy interpretations remain human-governed",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_constitutional_pluralism"
    assert record.meta.get("authoritative_worldview_selection_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("constitutional pluralism", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_constitutional_pluralism"
    assert "Constitutional Pluralism" in view.reply


def test_constitutional_pluralism_builds_from_legitimacy():
    session = "mc-pluralism-src-162"
    _full_stack(session)
    result = build_constitutional_pluralism(session_id=session)
    assert result.ok is True
    assert result.constitutional_pluralism["sources"]["constitutional_legitimacy"] is True
    assert len(result.constitutional_pluralism["pluralism_principles"]) >= 8
    assert len(result.constitutional_pluralism["sections"]["governance_perspective_mapping"]) >= 4
