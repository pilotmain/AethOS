# SPDX-License-Identifier: Apache-2.0
"""FIX 148 — governance deliberation workspace."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governance_deliberation.governance_deliberation_intent import (
    is_governance_deliberation_intent,
    parse_deliberation_record_intent,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_service import (
    build_governance_deliberation_workspace,
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
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_deliberation_records_for_tests()
    get_settings.cache_clear()


def test_governance_deliberation_intent():
    assert is_governance_deliberation_intent("show governance deliberation")
    assert is_governance_deliberation_intent("governance discussion timeline")
    assert not is_governance_deliberation_intent("auto approve now")


def test_deliberation_record_intent_parse():
    parsed = parse_deliberation_record_intent("deliberation note: blockers need human review")
    assert parsed == ("operator_note", "blockers need human review")


def test_governance_deliberation_api_readonly():
    session = "mc-deliberation-148"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governance-deliberation",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["governance_mutation_performed"] is False
    assert body["automatic_approval_enabled"] is False
    workspace = body["workspace"]
    assert workspace["schema_version"] == "mission_control_governance_deliberation_v1"
    sections = workspace["sections"]
    assert "governance_discussion_timeline" in sections
    assert "review_checklist" in sections
    assert "alternative_path_comparison" in sections
    assert "Governance Deliberation Workspace" in body["markdown"]


def test_governance_deliberation_record_persists_memory_only():
    session = "mc-deliberation-record-148"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governance-deliberation/record",
        json={
            "session_id": session,
            "kind": "operator_note",
            "content": "Operator reviewed blockers — defer until evidence complete.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["governance_mutation_performed"] is False
    assert body["deliberation_memory_only"] is True

    get_res = client.get("/api/v1/mission-control/governance-deliberation", params={"session_id": session})
    notes = get_res.json()["workspace"]["sections"]["operator_notes"]
    assert len(notes) == 1
    assert "defer until evidence" in notes[0]["content"]


def test_governance_deliberation_chat_view_and_record():
    session = "mc-deliberation-chat-148"
    _full_stack(session)
    record = resolve_chat_turn(
        "deliberation note: hold recommended pending approvals",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_governance_deliberation"
    assert record.meta.get("governance_mutation_performed") == "false"
    assert "Institutional governance memory" in record.reply

    view = resolve_chat_turn("show governance deliberation", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_governance_deliberation"
    assert "Governance Deliberation Workspace" in view.reply


def test_governance_deliberation_builds_from_readiness():
    session = "mc-deliberation-src-148"
    _full_stack(session)
    result = build_governance_deliberation_workspace(session_id=session)
    assert result.ok is True
    assert result.workspace["sources"]["mission_readiness_review"] is True
    assert len(result.workspace["sections"]["review_checklist"]) >= 8
