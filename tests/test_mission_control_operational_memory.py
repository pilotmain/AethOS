# SPDX-License-Identifier: Apache-2.0
"""FIX 139 — operational memory / knowledge graph (read-only)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.operational_memory.operational_memory_intent import is_operational_memory_intent
from aethos_core.mission_control.operational_memory.operational_memory_service import build_operational_memory_graph
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


def test_operational_memory_intent_detected():
    assert is_operational_memory_intent("show operational memory graph")
    assert is_operational_memory_intent("mission lineage for this session")
    assert not is_operational_memory_intent("auto-adapt from memory")


def test_operational_memory_api_readonly():
    session = "mc-op-memory-139"
    _full_stack(session)
    client = TestClient(app)
    res = client.get("/api/v1/mission-control/operational-memory", params={"session_id": session, "format": "both"})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_adaptation_enabled"] is False
    graph = body["graph"]
    assert graph["schema_version"] == "mission_control_operational_memory_v1"
    assert graph["graph"]["stats"]["node_count"] >= 1
    assert graph["mission_lineage"]
    assert graph["learning_signals"]
    assert "Operational Memory Graph" in body["markdown"]


def test_operational_memory_chat_route():
    session = "mc-op-memory-chat-139"
    _full_stack(session)
    result = resolve_chat_turn("show operational memory graph", session_id=session, apply_relational_layer=False)
    assert result.meta.get("route_id") == "mission_control_operational_memory"
    assert result.meta.get("mutation_performed") == "false"
    assert "Operational Memory Graph" in result.reply


def test_operational_memory_composes_sources():
    session = "mc-op-memory-src-139"
    _full_stack(session)
    graph = build_operational_memory_graph(session_id=session).graph
    sources = graph.get("sources") or {}
    assert sources.get("evidence_bundle") is True
