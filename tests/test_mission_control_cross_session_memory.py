# SPDX-License-Identifier: Apache-2.0
"""FIX 140 — cross-session operational memory persistence."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.operational_memory.cross_session.cross_session_intent import (
    is_cross_session_memory_intent,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_service import (
    build_cross_session_operational_memory,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
    list_operational_memory_records,
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


def test_cross_session_intent_detected():
    assert is_cross_session_memory_intent("show cross-session operational memory")
    assert is_cross_session_memory_intent("organizational memory layer")
    assert not is_cross_session_memory_intent("auto-adapt from memory")


def test_cross_session_persists_and_queries():
    session_a = "mc-xsess-a-140"
    session_b = "mc-xsess-b-140"
    _full_stack(session_a)
    build_cross_session_operational_memory(session_id=session_a, ingest_current=True)
    _full_stack(session_b)
    build_cross_session_operational_memory(session_id=session_b, ingest_current=True)

    records = list_operational_memory_records(limit=50)
    assert len(records) >= 2
    sessions = {r["session_id"] for r in records}
    assert session_a in sessions
    assert session_b in sessions


def test_cross_session_api_readonly():
    session = "mc-xsess-api-140"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/operational-memory/cross-session",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_adaptation_enabled"] is False
    assert body["autonomous_optimization_enabled"] is False
    memory = body["memory"]
    assert memory["schema_version"] == "mission_control_cross_session_memory_v1"
    org = memory["organizational_memory"]
    assert "operator_history" in org
    assert "evidence_stitching" in org
    assert "Cross-Session Operational Memory" in body["markdown"]


def test_cross_session_chat_route():
    session = "mc-xsess-chat-140"
    _full_stack(session)
    result = resolve_chat_turn("show cross-session operational memory", session_id=session, apply_relational_layer=False)
    assert result.meta.get("route_id") == "mission_control_cross_session_memory"
    assert result.meta.get("mutation_performed") == "false"
    assert "Cross-Session Operational Memory" in result.reply
