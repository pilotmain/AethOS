# SPDX-License-Identifier: Apache-2.0
"""FIX 149 — multi-operator governance collaboration."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governance_collaboration.governance_collaboration_intent import (
    is_governance_collaboration_intent,
    parse_collaboration_record_intent,
)
from aethos_core.mission_control.governance_collaboration.governance_collaboration_service import (
    build_governance_collaboration_workspace,
)
from aethos_core.mission_control.governance_collaboration.governance_collaboration_store import (
    clear_governance_collaboration_records_for_tests,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_store import (
    clear_governance_deliberation_records_for_tests,
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
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_deliberation_records_for_tests()
    clear_governance_collaboration_records_for_tests()
    get_settings.cache_clear()


def test_governance_collaboration_intent():
    assert is_governance_collaboration_intent("show governance collaboration")
    assert is_governance_collaboration_intent("multi-operator governance")
    assert not is_governance_collaboration_intent("auto quorum approve now")


def test_collaboration_record_intent_parse():
    parsed = parse_collaboration_record_intent("collaboration assign: alice owns readiness review")
    assert parsed == ("reviewer_assignment", "alice owns readiness review")


def test_governance_collaboration_api_readonly():
    session = "mc-collaboration-149"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governance-collaboration",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["delegated_execution_authority_enabled"] is False
    assert body["automatic_quorum_approval_enabled"] is False
    collaboration = body["collaboration"]
    assert collaboration["schema_version"] == "mission_control_governance_collaboration_v1"
    sections = collaboration["sections"]
    assert "named_reviewers" in sections
    assert "quorum_aware_discussion" in sections
    assert "decision_participation_graph" in sections
    assert "Multi-Operator Governance Collaboration" in body["markdown"]


def test_governance_collaboration_record_persists_memory_only():
    session = "mc-collaboration-record-149"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governance-collaboration/record",
        json={
            "session_id": session,
            "kind": "reviewer_acknowledgment",
            "content": "Reviewed blockers and evidence gaps.",
            "reviewer_name": "alice",
            "reviewer_role": "primary_reviewer",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["governance_mutation_performed"] is False
    assert body["collaboration_memory_only"] is True

    get_res = client.get("/api/v1/mission-control/governance-collaboration", params={"session_id": session})
    acks = get_res.json()["collaboration"]["sections"]["reviewer_acknowledgments"]
    assert len(acks) == 1
    assert acks[0]["reviewer_name"] == "alice"


def test_governance_collaboration_chat_view_and_record():
    session = "mc-collaboration-chat-149"
    _full_stack(session)
    record = resolve_chat_turn(
        "collaboration acknowledge: reviewed pending approvals",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_governance_collaboration"
    assert record.meta.get("delegated_execution_authority_enabled") == "false"
    assert "Institutional continuity" in record.reply

    view = resolve_chat_turn("show governance collaboration", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_governance_collaboration"
    assert "Multi-Operator Governance Collaboration" in view.reply


def test_governance_collaboration_builds_from_deliberation():
    session = "mc-collaboration-src-149"
    _full_stack(session)
    result = build_governance_collaboration_workspace(session_id=session)
    assert result.ok is True
    assert result.collaboration["sources"]["governance_deliberation"] is True
    quorum = result.collaboration["sections"]["quorum_aware_discussion"]
    assert quorum["automatic_quorum_approval"] is False
