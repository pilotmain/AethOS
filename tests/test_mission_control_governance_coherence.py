# SPDX-License-Identifier: Apache-2.0
"""FIX 153 — governance coherence + constitutional integrity."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governance_coherence.governance_coherence_intent import (
    is_governance_coherence_intent,
    parse_coherence_record_intent,
)
from aethos_core.mission_control.governance_coherence.governance_coherence_service import build_governance_coherence
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
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_store import (
    clear_governance_policy_interpretation_records_for_tests,
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
    get_settings.cache_clear()


def test_governance_coherence_intent():
    assert is_governance_coherence_intent("show governance coherence")
    assert is_governance_coherence_intent("constitutional integrity")
    assert not is_governance_coherence_intent("self-healing governance now")


def test_coherence_record_intent_parse():
    parsed = parse_coherence_record_intent(
        "coherence observation: precedent corpus diverges from session hold patterns"
    )
    assert parsed == (
        "coherence_observation",
        "precedent corpus diverges from session hold patterns",
    )


def test_governance_coherence_api_readonly():
    session = "mc-coherence-153"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governance-coherence",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_governance_correction_enabled"] is False
    assert body["self_healing_governance_enabled"] is False
    assert body["constitutional_override_authority_enabled"] is False
    coherence = body["coherence"]
    assert coherence["schema_version"] == "mission_control_governance_coherence_v1"
    sections = coherence["sections"]
    assert "doctrine_topology_consistency_analysis" in sections
    assert "institutional_integrity_scoring" in sections
    assert "governance_stability_indicators" in sections
    assert coherence["all_recommendations_executable"] is False
    assert "Governance Coherence" in body["markdown"]


def test_governance_coherence_record_persists():
    session = "mc-coherence-record-153"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governance-coherence/record",
        json={
            "session_id": session,
            "kind": "coherence_observation",
            "content": "Observed drift between session precedents and institutional hold doctrine.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["coherence_memory_only"] is True

    get_res = client.get("/api/v1/mission-control/governance-coherence", params={"session_id": session})
    records = get_res.json()["coherence"]["coherence_record_count"]
    assert records == 1


def test_governance_coherence_chat_view_and_record():
    session = "mc-coherence-chat-153"
    _full_stack(session)
    record = resolve_chat_turn(
        "coherence drift: hold precedent weight declining across sessions",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_governance_coherence"
    assert record.meta.get("autonomous_governance_correction_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("governance coherence", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_governance_coherence"
    assert "Governance Coherence" in view.reply


def test_governance_coherence_builds_from_interpretation():
    session = "mc-coherence-src-153"
    _full_stack(session)
    result = build_governance_coherence(session_id=session)
    assert result.ok is True
    assert result.coherence["sources"]["governance_policy_interpretation"] is True
    assert len(result.coherence["coherence_intelligence_principles"]) >= 8
    assert "integrity_score" in result.coherence["sections"]["institutional_integrity_scoring"]
