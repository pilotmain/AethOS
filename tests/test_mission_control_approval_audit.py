# SPDX-License-Identifier: Apache-2.0
"""FIX 134 — UI approval audit and replay protection."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.config import get_settings
from aethos_core.mission_control.approval_inbox.approval_audit_service import list_ui_approval_audits
from aethos_core.mission_control.approval_inbox.approval_execution_service import (
    clear_ui_approval_audit_for_tests,
    execute_governed_ui_approval,
)
from aethos_core.mission_control.approval_inbox.action_safety_review import review_mission_control_ui_action_safety
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


def test_action_safety_review_passes():
    review = review_mission_control_ui_action_safety()
    assert review["ok"] is True
    assert review["execution_path_violations"] == []


def test_replay_protection():
    session = "mc-replay-134"
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#80")
    create_implementation_plan(session_id=session)
    from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox

    inbox = build_approval_inbox(session_id=session)
    inbox_id = next(i["inbox_id"] for i in inbox.items if i["gate_id"] == "planning_approved")
    first = execute_governed_ui_approval(session_id=session, inbox_id=inbox_id)
    assert first.ok
    second = execute_governed_ui_approval(session_id=session, inbox_id=inbox_id)
    assert second.replay_protected
    assert second.outcome == "replay_protected"


def test_audit_api_lists_history():
    session = "mc-audit-api-134"
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#80")
    create_implementation_plan(session_id=session)
    from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox

    inbox_id = next(i["inbox_id"] for i in build_approval_inbox(session_id=session).items if i["gate_id"] == "planning_approved")
    execute_governed_ui_approval(session_id=session, inbox_id=inbox_id)
    client = TestClient(app)
    res = client.get("/api/v1/mission-control/approval-inbox/audit", params={"session_id": session})
    assert res.status_code == 200
    body = res.json()
    assert body["count"] >= 1
    assert body["audits"][0].get("route_id") is not None or body["audits"][0].get("chat_intent")
