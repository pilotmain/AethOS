# SPDX-License-Identifier: Apache-2.0
"""FIX 145 — mission strategy layer."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.mission_strategy.mission_strategy_intent import is_mission_strategy_intent
from aethos_core.mission_control.mission_strategy.mission_strategy_service import build_mission_strategy
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


def test_mission_strategy_intent():
    assert is_mission_strategy_intent("show mission strategy")
    assert is_mission_strategy_intent("strategic operational reasoning")
    assert not is_mission_strategy_intent("autonomous plan execution now")


def test_mission_strategy_api_readonly():
    session = "mc-strategy-145"
    _full_stack(session)
    client = TestClient(app)
    res = client.get("/api/v1/mission-control/mission-strategy", params={"session_id": session, "format": "both"})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_planning_enabled"] is False
    assert body["organizational_self_direction_enabled"] is False
    strategy = body["strategy"]
    assert strategy["schema_version"] == "mission_control_mission_strategy_v1"
    sections = strategy["sections"]
    assert "long_running_mission_themes" in sections
    assert "organizational_risk_concentration" in sections
    assert strategy["all_recommendations_executable"] is False
    assert "Mission Strategy Layer" in body["markdown"]


def test_mission_strategy_chat_route():
    session = "mc-strategy-chat-145"
    _full_stack(session)
    result = resolve_chat_turn("show mission strategy", session_id=session, apply_relational_layer=False)
    assert result.meta.get("route_id") == "mission_control_mission_strategy"
    assert result.meta.get("mutation_performed") == "false"
    assert "Mission Strategy Layer" in result.reply


def test_mission_strategy_builds_from_sources():
    session = "mc-strategy-src-145"
    _full_stack(session)
    result = build_mission_strategy(session_id=session)
    assert result.ok is True
    assert result.strategy["sources"]["governance_simulation"] is True
