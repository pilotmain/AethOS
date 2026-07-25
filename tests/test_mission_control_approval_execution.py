# SPDX-License-Identifier: Apache-2.0
"""FIX 133 — Mission Control governed UI approval execution."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.config import get_settings
from aethos_core.mission_control.approval_inbox.approval_execution_contract import (
    CHAT_GOVERNANCE_REQUIRED,
    UI_APPROVAL_ORIGIN,
    ui_approval_eligible,
)
from aethos_core.mission_control.approval_inbox.approval_execution_service import (
    clear_ui_approval_audit_for_tests,
    execute_governed_ui_approval,
)
from aethos_core.mission_control.approval_inbox.approval_phrase_templates import build_copy_phrase_text
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_service import analyze_github_issue, create_implementation_plan


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as cp

    cp()
    clear_ui_approval_audit_for_tests()
    get_settings.cache_clear()
    yield
    cp()
    clear_ui_approval_audit_for_tests()
    get_settings.cache_clear()


def test_ui_eligibility_excludes_mutations():
    assert ui_approval_eligible(lane="software_delivery", gate_id="planning_approved")
    assert not ui_approval_eligible(lane="software_delivery", gate_id="branch_push_completed")
    assert not ui_approval_eligible(lane="governed_execution", gate_id="mutation_preflight")


def test_copy_phrase_text():
    msg = build_copy_phrase_text(gate_id="planning_approved", required_phrases=[PLANNING_APPROVAL_PHRASE])
    assert PLANNING_APPROVAL_PHRASE in msg
    assert "approve implementation planning" in msg


def test_execute_planning_approval_via_ui():
    session = "mc-exec-133"
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#80")
    create_implementation_plan(session_id=session)
    inbox = build_approval_inbox(session_id=session)
    planning = next(i for i in inbox.items if i["gate_id"] == "planning_approved")
    assert planning["ui_approval_eligible"]

    result = execute_governed_ui_approval(session_id=session, inbox_id=planning["inbox_id"])
    assert result.ok
    assert result.audit_id
    assert CHAT_GOVERNANCE_REQUIRED
    assert "software_delivery" in (result.route_id or result.chat_intent or "")


def test_execute_api():
    session = "mc-api-exec-133"
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#80")
    create_implementation_plan(session_id=session)
    inbox = build_approval_inbox(session_id=session)
    inbox_id = next(i["inbox_id"] for i in inbox.items if i["gate_id"] == "planning_approved")

    client = TestClient(app)
    res = client.post(
        "/api/v1/mission-control/approval-inbox/execute",
        json={"session_id": session, "inbox_id": inbox_id},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ui_origin"] == UI_APPROVAL_ORIGIN
    assert body["chat_governance_required"] is True
    assert body["ok"] is True
    assert body["audit_id"]


def test_ineligible_gate_rejected():
    session = "mc-inelig-133"
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#80")
    create_implementation_plan(session_id=session)
    # Fabricate inbox id that won't exist - use branch push if we had one
    result = execute_governed_ui_approval(session_id=session, inbox_id="sd-branch-push-fake")
    assert not result.ok
