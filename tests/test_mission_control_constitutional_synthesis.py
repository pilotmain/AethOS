# SPDX-License-Identifier: Apache-2.0
"""FIX 163 — constitutional synthesis + institutional wisdom."""

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
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_store import (
    clear_constitutional_pluralism_records_for_tests,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_intent import (
    is_constitutional_synthesis_intent,
    parse_synthesis_record_intent,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_service import (
    build_constitutional_synthesis,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_store import (
    clear_constitutional_synthesis_records_for_tests,
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
    clear_constitutional_synthesis_records_for_tests()
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
    get_settings.cache_clear()


def test_constitutional_synthesis_intent():
    assert is_constitutional_synthesis_intent("show constitutional synthesis")
    assert is_constitutional_synthesis_intent("constitutional tension")
    assert not is_constitutional_synthesis_intent("autonomous constitutional decisions now")


def test_synthesis_record_intent_parse():
    parsed = parse_synthesis_record_intent(
        "synthesis tension: ethics and resilience may tension under stress without autonomous resolution"
    )
    assert parsed == (
        "tension_analysis_note",
        "ethics and resilience may tension under stress without autonomous resolution",
    )


def test_constitutional_synthesis_api_readonly():
    session = "mc-synthesis-163"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/constitutional-synthesis",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_constitutional_decisions_enabled"] is False
    assert body["doctrine_enforcement_enabled"] is False
    constitutional_synthesis = body["constitutional_synthesis"]
    assert constitutional_synthesis["schema_version"] == "mission_control_constitutional_synthesis_v1"
    sections = constitutional_synthesis["sections"]
    assert "constitutional_tension_analysis" in sections
    assert "constitutional_tradeoff_maps" in sections
    assert "cross_dimensional_synthesis" in sections
    assert constitutional_synthesis["all_recommendations_executable"] is False
    assert "Constitutional Synthesis" in body["markdown"]


def test_constitutional_synthesis_record_persists():
    session = "mc-synthesis-record-163"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/constitutional-synthesis/record",
        json={
            "session_id": session,
            "kind": "tension_analysis_note",
            "content": "Ethics vs resilience tension surfaced for human constitutional stewardship.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["constitutional_synthesis_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/constitutional-synthesis",
        params={"session_id": session},
    )
    assert get_res.json()["constitutional_synthesis"]["synthesis_record_count"] == 1


def test_constitutional_synthesis_chat_view_and_record():
    session = "mc-synthesis-chat-163"
    _full_stack(session)
    record = resolve_chat_turn(
        "synthesis wisdom: recurring constitutional tensions require cross-dimensional human review",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_constitutional_synthesis"
    assert record.meta.get("autonomous_constitutional_decisions_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("constitutional synthesis", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_constitutional_synthesis"
    assert "Constitutional Synthesis" in view.reply


def test_constitutional_synthesis_builds_from_pluralism_and_audit():
    session = "mc-synthesis-src-163"
    _full_stack(session)
    result = build_constitutional_synthesis(session_id=session)
    assert result.ok is True
    assert result.constitutional_synthesis["sources"]["constitutional_pluralism"] is True
    assert result.constitutional_synthesis["sources"]["constitutional_audit"] is True
    assert len(result.constitutional_synthesis["synthesis_principles"]) >= 8
    assert len(result.constitutional_synthesis["sections"]["constitutional_tension_analysis"]) >= 4
