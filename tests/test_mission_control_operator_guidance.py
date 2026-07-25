# SPDX-License-Identifier: Apache-2.0
"""FIX 142 — operator contextual guidance (recommendation-only)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.operator_guidance.operator_guidance_intent import is_operator_guidance_intent
from aethos_core.mission_control.operator_guidance.operator_guidance_service import build_operator_contextual_guidance
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
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    get_settings.cache_clear()


def test_operator_guidance_intent():
    assert is_operator_guidance_intent("show operator guidance")
    assert is_operator_guidance_intent("what should I do next")
    assert not is_operator_guidance_intent("auto execute recommendations now")


def test_operator_guidance_api_readonly():
    session = "mc-guidance-142"
    _full_stack(session)
    client = TestClient(app)
    res = client.get("/api/v1/mission-control/operator-guidance", params={"session_id": session, "format": "both"})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_execution_enabled"] is False
    guidance = body["guidance"]
    assert guidance["schema_version"] == "mission_control_operator_guidance_v1"
    assert guidance["all_recommendations_executable"] is False
    sections = guidance["sections"]
    assert "likely_next_governed_steps" in sections
    assert "rollout_caution" in sections
    for items in sections.values():
        for item in items:
            assert item["executable"] is False
            assert item["operator_approval_required"] is True
    assert "Operator Contextual Guidance" in body["markdown"]


def test_operator_guidance_chat_route():
    session = "mc-guidance-chat-142"
    _full_stack(session)
    result = resolve_chat_turn("show operator guidance", session_id=session, apply_relational_layer=False)
    assert result.meta.get("route_id") == "mission_control_operator_guidance"
    assert result.meta.get("mutation_performed") == "false"
    assert "Operator Contextual Guidance" in result.reply


def test_operator_guidance_sections_populated():
    session = "mc-guidance-sections-142"
    _full_stack(session)
    result = build_operator_contextual_guidance(session_id=session)
    assert result.ok is True
    assert result.guidance.get("recommendation_count", 0) >= 1
