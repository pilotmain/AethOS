# SPDX-License-Identifier: Apache-2.0
"""FIX 141 — mission knowledge spaces semantic retrieval."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_intent import is_knowledge_spaces_intent
from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_service import search_mission_knowledge_spaces
from aethos_core.mission_control.knowledge_spaces.semantic_retrieval import semantic_similarity
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


def test_semantic_similarity_overlap():
    score = semantic_similarity(query="open incident blocker", document_text="production incident open blocker")
    assert score >= 0.4


def test_knowledge_spaces_intent():
    assert is_knowledge_spaces_intent("have we seen this blocker before")
    assert is_knowledge_spaces_intent("semantic search incidents")
    assert not is_knowledge_spaces_intent("auto execute mutation now")


def test_knowledge_spaces_api_readonly():
    session = "mc-knowledge-141"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/knowledge-spaces/search",
        params={"session_id": session, "q": "blocker approval gate", "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["autonomous_action_enabled"] is False
    search = body["search"]
    assert search["schema_version"] == "mission_control_knowledge_spaces_v1"
    assert "seen_before" in search
    assert "recommendations" in search
    assert all(r.get("executable") is False for r in search["recommendations"])
    assert "Mission Knowledge Spaces" in body["markdown"]


def test_knowledge_spaces_chat_route():
    session = "mc-knowledge-chat-141"
    _full_stack(session)
    result = resolve_chat_turn(
        "semantic search blockers and approvals",
        session_id=session,
        apply_relational_layer=False,
    )
    assert result.meta.get("route_id") == "mission_control_knowledge_spaces"
    assert result.meta.get("mutation_performed") == "false"
    assert "Mission Knowledge Spaces" in result.reply


def test_knowledge_spaces_search_after_ingest():
    session = "mc-knowledge-ingest-141"
    _full_stack(session)
    result = search_mission_knowledge_spaces(
        session_id=session,
        query="software delivery gate planning",
        ingest_current=True,
    )
    assert result.ok is True
    assert result.payload.get("document_corpus_size", 0) >= 1
