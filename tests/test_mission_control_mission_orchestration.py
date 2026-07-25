# SPDX-License-Identifier: Apache-2.0
"""FIX 146 — coordinated mission orchestration."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.mission_orchestration.mission_orchestration_intent import (
    is_mission_orchestration_intent,
)
from aethos_core.mission_control.mission_orchestration.mission_orchestration_service import (
    build_mission_orchestration,
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
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    get_settings.cache_clear()


def test_mission_orchestration_intent():
    assert is_mission_orchestration_intent("show mission orchestration")
    assert is_mission_orchestration_intent("orchestration readiness")
    assert not is_mission_orchestration_intent("autonomous sequencing execute now")


def test_mission_orchestration_api_readonly():
    session = "mc-orchestration-146"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/mission-orchestration",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_orchestration_enabled"] is False
    assert body["autonomous_sequencing_execution_enabled"] is False
    orchestration = body["orchestration"]
    assert orchestration["schema_version"] == "mission_control_mission_orchestration_v1"
    sections = orchestration["sections"]
    assert "mission_dependency_graph" in sections
    assert "orchestration_readiness_scoring" in sections
    assert "cross_lane_mission_health" in sections
    assert orchestration["all_recommendations_executable"] is False
    assert "Coordinated Mission Orchestration" in body["markdown"]


def test_mission_orchestration_chat_route():
    session = "mc-orchestration-chat-146"
    _full_stack(session)
    result = resolve_chat_turn("show mission orchestration", session_id=session, apply_relational_layer=False)
    assert result.meta.get("route_id") == "mission_control_mission_orchestration"
    assert result.meta.get("mutation_performed") == "false"
    assert "Coordinated Mission Orchestration" in result.reply


def test_mission_orchestration_builds_from_sources():
    session = "mc-orchestration-src-146"
    _full_stack(session)
    result = build_mission_orchestration(session_id=session)
    assert result.ok is True
    assert result.orchestration["sources"]["cross_lane_snapshot"] is True
    assert result.orchestration["sources"]["mission_strategy"] is True
