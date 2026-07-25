# SPDX-License-Identifier: Apache-2.0
"""FIX 151 — governance doctrine + policy charter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governance_collaboration.governance_collaboration_store import (
    clear_governance_collaboration_records_for_tests,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_store import (
    clear_governance_deliberation_records_for_tests,
)
from aethos_core.mission_control.governance_doctrine.governance_doctrine_intent import (
    is_governance_doctrine_intent,
    parse_doctrine_record_intent,
)
from aethos_core.mission_control.governance_doctrine.governance_doctrine_service import build_governance_doctrine
from aethos_core.mission_control.governance_doctrine.governance_doctrine_store import (
    clear_governance_doctrine_records_for_tests,
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
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_deliberation_records_for_tests()
    clear_governance_collaboration_records_for_tests()
    clear_governance_doctrine_records_for_tests()
    get_settings.cache_clear()


def test_governance_doctrine_intent():
    assert is_governance_doctrine_intent("show governance doctrine")
    assert is_governance_doctrine_intent("policy charter")
    assert not is_governance_doctrine_intent("autonomous doctrine evolution now")


def test_doctrine_record_intent_parse():
    parsed = parse_doctrine_record_intent("doctrine amendment: extend review quorum advisory to three reviewers")
    assert parsed == (
        "policy_amendment_proposal",
        "extend review quorum advisory to three reviewers",
    )


def test_governance_doctrine_api_readonly():
    session = "mc-doctrine-151"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governance-doctrine",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["automatic_policy_mutation_enabled"] is False
    assert body["autonomous_doctrine_evolution_enabled"] is False
    doctrine = body["doctrine"]
    assert doctrine["schema_version"] == "mission_control_governance_doctrine_v1"
    sections = doctrine["sections"]
    assert "governance_principle_registry" in sections
    assert "doctrine_conflict_detection" in sections
    assert "constitutional_governance_references" in sections
    assert doctrine["all_amendments_executable"] is False
    assert "Governance Doctrine" in body["markdown"]


def test_governance_doctrine_amendment_proposal_persists():
    session = "mc-doctrine-record-151"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governance-doctrine/record",
        json={
            "session_id": session,
            "kind": "policy_amendment_proposal",
            "content": "Propose extending evidence bundle export before readiness go recommendation.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["doctrine_memory_only"] is True

    get_res = client.get("/api/v1/mission-control/governance-doctrine", params={"session_id": session})
    proposals = get_res.json()["doctrine"]["sections"]["policy_amendment_proposals"]
    assert len(proposals) == 1
    assert proposals[0]["executable"] is False


def test_governance_doctrine_chat_view_and_record():
    session = "mc-doctrine-chat-151"
    _full_stack(session)
    record = resolve_chat_turn(
        "doctrine precedent: hold pattern used when incident exposure elevated",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_governance_doctrine"
    assert record.meta.get("autonomous_doctrine_evolution_enabled") == "false"
    assert "Amendment proposals only" in record.reply

    view = resolve_chat_turn("governance doctrine", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_governance_doctrine"
    assert "Governance Doctrine" in view.reply


def test_governance_doctrine_builds_from_topology():
    session = "mc-doctrine-src-151"
    _full_stack(session)
    result = build_governance_doctrine(session_id=session)
    assert result.ok is True
    assert result.doctrine["sources"]["governance_role_architecture"] is True
    assert len(result.doctrine["sections"]["governance_principle_registry"]) >= 7
