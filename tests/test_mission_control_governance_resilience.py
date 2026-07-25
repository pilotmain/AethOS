# SPDX-License-Identifier: Apache-2.0
"""FIX 154 — governance resilience + stress simulation."""

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
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_store import (
    clear_governance_policy_interpretation_records_for_tests,
)
from aethos_core.mission_control.governance_resilience.governance_resilience_intent import (
    is_governance_resilience_intent,
    parse_resilience_record_intent,
)
from aethos_core.mission_control.governance_resilience.governance_resilience_service import build_governance_resilience
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
    get_settings.cache_clear()


def test_governance_resilience_intent():
    assert is_governance_resilience_intent("show governance resilience")
    assert is_governance_resilience_intent("approval chain overload")
    assert not is_governance_resilience_intent("self-healing governance now")


def test_resilience_record_intent_parse():
    parsed = parse_resilience_record_intent(
        "resilience scenario: simulate quorum failure under incident surge conditions"
    )
    assert parsed == (
        "stress_scenario",
        "simulate quorum failure under incident surge conditions",
    )


def test_governance_resilience_api_readonly():
    session = "mc-resilience-154"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governance-resilience",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["simulation_only"] is True
    assert body["mutation_performed"] is False
    assert body["automatic_governance_adaptation_enabled"] is False
    assert body["autonomous_resilience_correction_enabled"] is False
    assert body["self_healing_governance_enabled"] is False
    resilience = body["resilience"]
    assert resilience["schema_version"] == "mission_control_governance_resilience_v1"
    sections = resilience["sections"]
    assert "governance_stress_scenarios" in sections
    assert "institutional_resilience_scoring" in sections
    assert "trust_boundary_breach_simulation" in sections
    assert resilience["all_simulations_executable"] is False
    assert "Governance Resilience" in body["markdown"]


def test_governance_resilience_record_persists():
    session = "mc-resilience-record-154"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governance-resilience/record",
        json={
            "session_id": session,
            "kind": "resilience_observation",
            "content": "Simulated approval-chain overload under concurrent gate pressure.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["simulation_only"] is True
    assert body["resilience_memory_only"] is True

    get_res = client.get("/api/v1/mission-control/governance-resilience", params={"session_id": session})
    assert get_res.json()["resilience"]["resilience_record_count"] == 1


def test_governance_resilience_chat_view_and_record():
    session = "mc-resilience-chat-154"
    _full_stack(session)
    record = resolve_chat_turn(
        "resilience observation: handoff continuity stressed under operator loss simulation",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_governance_resilience"
    assert record.meta.get("autonomous_resilience_correction_enabled") == "false"
    assert record.meta.get("simulation_only") == "true"
    assert "Simulation-only" in record.reply

    view = resolve_chat_turn("governance resilience", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_governance_resilience"
    assert "Governance Resilience" in view.reply


def test_governance_resilience_builds_from_coherence():
    session = "mc-resilience-src-154"
    _full_stack(session)
    result = build_governance_resilience(session_id=session)
    assert result.ok is True
    assert result.resilience["sources"]["governance_coherence"] is True
    assert len(result.resilience["resilience_cognition_principles"]) >= 8
    assert "resilience_score" in result.resilience["sections"]["institutional_resilience_scoring"]
