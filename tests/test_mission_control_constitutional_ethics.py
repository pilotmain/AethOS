# SPDX-License-Identifier: Apache-2.0
"""FIX 159 — constitutional ethics + institutional moral reasoning."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_intent import (
    is_constitutional_ethics_intent,
    parse_ethics_record_intent,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_service import (
    build_constitutional_ethics,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_store import (
    clear_constitutional_ethics_records_for_tests,
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
    get_settings.cache_clear()


def test_constitutional_ethics_intent():
    assert is_constitutional_ethics_intent("show constitutional ethics")
    assert is_constitutional_ethics_intent("moral tradeoff analysis")
    assert not is_constitutional_ethics_intent("autonomous moral authority now")


def test_ethics_record_intent_parse():
    parsed = parse_ethics_record_intent(
        "ethical conflict: mission urgency pressures governance safety under constitutional intent"
    )
    assert parsed == (
        "value_conflict_note",
        "mission urgency pressures governance safety under constitutional intent",
    )


def test_constitutional_ethics_api_readonly():
    session = "mc-ethics-159"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/constitutional-ethics",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_moral_authority_enabled"] is False
    assert body["value_enforcement_authority_enabled"] is False
    constitutional_ethics = body["constitutional_ethics"]
    assert constitutional_ethics["schema_version"] == "mission_control_constitutional_ethics_v1"
    sections = constitutional_ethics["sections"]
    assert "constitutional_ethics_records" in sections
    assert "ethical_coherence_scoring" in sections
    assert "constitutional_value_drift_detection" in sections
    assert constitutional_ethics["all_recommendations_executable"] is False
    assert "Constitutional Ethics" in body["markdown"]


def test_constitutional_ethics_record_persists():
    session = "mc-ethics-record-159"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/constitutional-ethics/record",
        json={
            "session_id": session,
            "kind": "value_preservation_note",
            "content": "Preserve human sovereignty over all moral tradeoff resolution.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["constitutional_ethics_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/constitutional-ethics",
        params={"session_id": session},
    )
    assert get_res.json()["constitutional_ethics"]["ethics_record_count"] == 1


def test_constitutional_ethics_chat_view_and_record():
    session = "mc-ethics-chat-159"
    _full_stack(session)
    record = resolve_chat_turn(
        "ethical preservation: human moral sovereignty over value conflicts under mission pressure",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_constitutional_ethics"
    assert record.meta.get("autonomous_moral_authority_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("constitutional ethics", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_constitutional_ethics"
    assert "Constitutional Ethics" in view.reply


def test_constitutional_ethics_builds_from_existential_risk():
    session = "mc-ethics-src-159"
    _full_stack(session)
    result = build_constitutional_ethics(session_id=session)
    assert result.ok is True
    assert result.constitutional_ethics["sources"]["institutional_existential_risk"] is True
    assert len(result.constitutional_ethics["ethics_principles"]) >= 8
    assert len(result.constitutional_ethics["sections"]["value_conflict_reasoning"]) >= 4
