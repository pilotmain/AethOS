# SPDX-License-Identifier: Apache-2.0
"""FIX 132 — Mission Control approval inbox (view-only)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.config import get_settings
from aethos_core.mission_control.approval_inbox.approval_inbox_contract import (
    APPROVAL_EXECUTION_ENABLED_FIX_133,
    MUTATION_PERFORMED_FIX_132,
)
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_service import analyze_github_issue, create_implementation_plan
from aethos_core.software_delivery.github_pr_preflight_contract import GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE
from aethos_core.software_delivery.github_pr_preflight_service import run_github_pr_creation_preflight
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as cp

    cp()
    get_settings.cache_clear()
    yield
    cp()
    get_settings.cache_clear()


def test_approval_inbox_contract():
    assert MUTATION_PERFORMED_FIX_132 is False
    assert APPROVAL_EXECUTION_ENABLED_FIX_133 is True


def test_inbox_planning_approval_pending():
    session = "mc-inbox-plan-132"
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#80")
    create_implementation_plan(session_id=session)
    result = build_approval_inbox(session_id=session)
    assert result.ok
    planning = [i for i in result.items if i.get("gate_id") == "planning_approved"]
    assert planning
    assert PLANNING_APPROVAL_PHRASE in planning[0]["required_phrases"]


def test_inbox_after_verification_shows_preflight_approval():
    from aethos_core.software_delivery.pr_draft_service import create_software_delivery_pr_draft
    from aethos_core.software_delivery.workspace_verification_service import run_workspace_verification

    session = "mc-inbox-132"
    _full_stack(session)
    run_workspace_verification(session_id=session)
    create_software_delivery_pr_draft(session_id=session)
    preflight = run_github_pr_creation_preflight(session_id=session)
    assert preflight.ok
    result = build_approval_inbox(session_id=session)
    assert result.ok
    preflight_items = [i for i in result.items if i.get("gate_id") == "github_preflight_approved"]
    assert preflight_items
    assert GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE in preflight_items[0]["required_phrases"]
    assert preflight_items[0]["unlocks"]
    assert preflight_items[0]["remains_forbidden"]


def test_inbox_groups_by_lane():
    session = "mc-inbox-grp-132"
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#80")
    create_implementation_plan(session_id=session)
    result = build_approval_inbox(session_id=session)
    assert any(g.get("lane") == "software_delivery" for g in result.groups)


def test_approval_inbox_api():
    session = "mc-api-inbox-132"
    analyze_github_issue(session_id=session, user_text="analyze github issue pilotmain/AethOS#80")
    create_implementation_plan(session_id=session)
    client = TestClient(app)
    res = client.get("/api/v1/mission-control/approval-inbox", params={"session_id": session})
    assert res.status_code == 200
    body = res.json()
    assert body["read_only"] is True
    assert body["approval_execution_enabled"] is True
    assert body["mutation_performed"] is False
    assert body["summary"]["total_pending"] >= 1
