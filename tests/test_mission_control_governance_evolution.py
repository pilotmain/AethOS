# SPDX-License-Identifier: Apache-2.0
"""FIX 155 — governance evolution + institutional continuity."""

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
from aethos_core.mission_control.governance_evolution.governance_evolution_intent import (
    is_governance_evolution_intent,
    parse_evolution_record_intent,
)
from aethos_core.mission_control.governance_evolution.governance_evolution_service import build_governance_evolution
from aethos_core.mission_control.governance_evolution.governance_evolution_store import (
    clear_governance_evolution_records_for_tests,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_store import (
    clear_governance_policy_interpretation_records_for_tests,
)
from aethos_core.mission_control.governance_resilience.governance_resilience_store import (
    clear_governance_resilience_records_for_tests,
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
    get_settings.cache_clear()


def test_governance_evolution_intent():
    assert is_governance_evolution_intent("show governance evolution")
    assert is_governance_evolution_intent("doctrine era")
    assert not is_governance_evolution_intent("autonomous governance evolution now")


def test_evolution_record_intent_parse():
    parsed = parse_evolution_record_intent(
        "evolution era: constitutional governance era beginning FIX 150 institutional topology"
    )
    assert parsed == (
        "doctrine_era",
        "constitutional governance era beginning FIX 150 institutional topology",
    )


def test_governance_evolution_api_readonly():
    session = "mc-evolution-155"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governance-evolution",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_governance_evolution_enabled"] is False
    assert body["automatic_doctrine_migration_enabled"] is False
    assert body["policy_mutation_authority_enabled"] is False
    evolution = body["evolution"]
    assert evolution["schema_version"] == "mission_control_governance_evolution_v1"
    sections = evolution["sections"]
    assert "doctrine_era_tracking" in sections
    assert "institutional_continuity_scoring" in sections
    assert "historical_governance_narrative_reconstruction" in sections
    assert evolution["all_recommendations_executable"] is False
    assert "Governance Evolution" in body["markdown"]


def test_governance_evolution_record_persists():
    session = "mc-evolution-record-155"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governance-evolution/record",
        json={
            "session_id": session,
            "kind": "continuity_observation",
            "content": "Observed transition from operational to constitutional governance era.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["evolution_memory_only"] is True

    get_res = client.get("/api/v1/mission-control/governance-evolution", params={"session_id": session})
    assert get_res.json()["evolution"]["evolution_record_count"] == 1


def test_governance_evolution_chat_view_and_record():
    session = "mc-evolution-chat-155"
    _full_stack(session)
    record = resolve_chat_turn(
        "evolution continuity: freeze-era baseline maintained across constitutional FIX progression",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_governance_evolution"
    assert record.meta.get("autonomous_governance_evolution_enabled") == "false"
    assert "Recommendation-only" in record.reply

    view = resolve_chat_turn("governance evolution", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_governance_evolution"
    assert "Governance Evolution" in view.reply


def test_governance_evolution_builds_from_resilience():
    session = "mc-evolution-src-155"
    _full_stack(session)
    result = build_governance_evolution(session_id=session)
    assert result.ok is True
    assert result.evolution["sources"]["governance_resilience"] is True
    assert len(result.evolution["temporal_cognition_principles"]) >= 8
    assert "continuity_score" in result.evolution["sections"]["institutional_continuity_scoring"]
