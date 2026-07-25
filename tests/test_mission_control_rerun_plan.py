# SPDX-License-Identifier: Apache-2.0
"""FIX 138 — governed rerun planning (chat-only)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.rerun_planning.rerun_plan_intent import is_governed_rerun_plan_intent
from aethos_core.mission_control.rerun_planning.rerun_plan_service import build_governed_rerun_plan
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.approval_inbox.approval_execution_service import clear_ui_approval_audit_for_tests
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    get_settings.cache_clear()


def test_rerun_plan_intent_detected():
    assert is_governed_rerun_plan_intent("show governed rerun plan")
    assert is_governed_rerun_plan_intent("what would happen if we rerun this flow")
    assert not is_governed_rerun_plan_intent("execute rerun now")


def test_rerun_plan_api_readonly():
    session = "mc-rerun-plan-138"
    _full_stack(session)
    client = TestClient(app)
    res = client.get("/api/v1/mission-control/rerun-plan", params={"session_id": session, "format": "both"})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["rerun_execution_enabled"] is False
    plan = body["plan"]
    assert plan["schema_version"] == "mission_control_rerun_plan_v1"
    assert plan["eligibility"]["eligible_for_execution"] is False
    assert plan["replay_derived_plan"]["target_step_index"] is not None
    assert plan["blast_radius"]
    assert plan["dependencies"]
    assert plan["stale_state"]
    assert plan["rollback_posture"]
    assert plan["mutation_preview"]["execution_enabled"] is False
    assert plan["exact_rerun_phrases"]
    assert all(p["executable"] is False for p in plan["exact_rerun_phrases"])
    assert "Governed Rerun Plan" in body["markdown"]


def test_rerun_plan_chat_route():
    session = "mc-rerun-chat-138"
    _full_stack(session)
    result = resolve_chat_turn("show governed rerun plan", session_id=session, apply_relational_layer=False)
    assert result.meta.get("route_id") == "mission_control_rerun_plan"
    assert result.meta.get("mutation_performed") == "false"
    assert "Governed Rerun Plan" in result.reply
    assert "planning only" in result.reply.lower() or "FIX 138" in result.reply


def test_rerun_plan_blockers_include_execution_disabled():
    session = "mc-rerun-block-138"
    _full_stack(session)
    plan = build_governed_rerun_plan(session_id=session).plan
    codes = {b["code"] for b in plan.get("rerun_blockers") or []}
    assert "rerun_execution_disabled" in codes
