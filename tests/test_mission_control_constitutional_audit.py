# SPDX-License-Identifier: Apache-2.0
"""FIX 160 — constitutional audit + public accountability."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.constitutional_audit.constitutional_audit_intent import (
    is_constitutional_audit_intent,
    parse_audit_record_intent,
)
from aethos_core.mission_control.constitutional_audit.constitutional_audit_service import (
    build_constitutional_audit,
)
from aethos_core.mission_control.constitutional_audit.constitutional_audit_store import (
    clear_constitutional_audit_records_for_tests,
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
    clear_constitutional_audit_records_for_tests()
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
    get_settings.cache_clear()


def test_constitutional_audit_intent():
    assert is_constitutional_audit_intent("show constitutional audit")
    assert is_constitutional_audit_intent("public accountability")
    assert not is_constitutional_audit_intent("autonomous disclosure now")


def test_audit_record_intent_parse():
    parsed = parse_audit_record_intent(
        "audit explanation: recommendation derived from bounded constitutional cognition layers only"
    )
    assert parsed == (
        "recommendation_explanation",
        "recommendation derived from bounded constitutional cognition layers only",
    )


def test_constitutional_audit_api_readonly():
    session = "mc-audit-160"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/constitutional-audit",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_disclosure_enabled"] is False
    assert body["public_communication_authority_enabled"] is False
    constitutional_audit = body["constitutional_audit"]
    assert constitutional_audit["schema_version"] == "mission_control_constitutional_audit_v1"
    sections = constitutional_audit["sections"]
    assert "constitutional_audit_reports" in sections
    assert "recommendation_explanations" in sections
    assert "audit_trail_integrity_checks" in sections
    assert constitutional_audit["all_recommendations_executable"] is False
    assert "Constitutional Audit" in body["markdown"]


def test_constitutional_audit_record_persists():
    session = "mc-audit-record-160"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/constitutional-audit/record",
        json={
            "session_id": session,
            "kind": "accountability_record",
            "content": "Human operators govern all disclosure and enforcement decisions.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["constitutional_audit_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/constitutional-audit",
        params={"session_id": session},
    )
    assert get_res.json()["constitutional_audit"]["audit_record_count"] == 1


def test_constitutional_audit_chat_view_and_record():
    session = "mc-audit-chat-160"
    _full_stack(session)
    record = resolve_chat_turn(
        "audit accountability: human governance over disclosure and enforcement of constitutional recommendations",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_constitutional_audit"
    assert record.meta.get("autonomous_disclosure_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("constitutional audit", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_constitutional_audit"
    assert "Constitutional Audit" in view.reply


def test_constitutional_audit_builds_from_ethics():
    session = "mc-audit-src-160"
    _full_stack(session)
    result = build_constitutional_audit(session_id=session)
    assert result.ok is True
    assert result.constitutional_audit["sources"]["constitutional_ethics"] is True
    assert len(result.constitutional_audit["accountability_principles"]) >= 8
    assert len(result.constitutional_audit["sections"]["doctrine_ethics_existential_linkage"]) >= 10
