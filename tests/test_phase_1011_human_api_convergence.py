# SPDX-License-Identifier: Apache-2.0
"""Phase 10.1.1 — Human API convergence and living intelligence reliability."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.conversation_runtime import clear_conversation_for_tests, record_conversation_thread
from aethos_core.conversation.operational_memory import clear_operational_memory_for_tests, load_operational_memory
from aethos_core.human_centered.human_route_registry import discover_human_routes
from aethos_core.human_centered.human_runtime_replay import clear_human_runtime_artifacts_for_tests, get_human_runtime_replay
from aethos_core.presence.live.live_presence_runtime import build_contextual_nudge, clear_live_presence_for_tests, record_focus
from aethos_core.runtime.runtime_integrity.runtime_health import build_runtime_integrity_report


@pytest.fixture(autouse=True)
def _clean():
    clear_live_presence_for_tests()
    clear_conversation_for_tests()
    clear_operational_memory_for_tests()
    clear_human_runtime_artifacts_for_tests()
    yield
    clear_live_presence_for_tests()
    clear_conversation_for_tests()
    clear_operational_memory_for_tests()
    clear_human_runtime_artifacts_for_tests()


def test_human_living_route_mounted():
    client = TestClient(app)
    r = client.get("/api/v1/human/living?session_id=default")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("phase") in ("10.1", "10.1.1", "10.1.2", "10.1.3", "10.1.4")


def test_human_routes_discovery_healthy():
    client = TestClient(app)
    r = client.get("/api/v1/human/routes")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("health") == "healthy"
    assert body.get("missing_routes") == []


def test_discover_human_routes_registry():
    discovery = discover_human_routes(app=app)
    paths = {item["path"] for item in discovery.get("mounted_routes") or []}
    assert "/human/living" in paths
    assert "/human/routes" in paths


def test_runtime_integrity_report_healthy():
    report = build_runtime_integrity_report(app=app)
    assert report.get("health") == "healthy"
    labels = [c.get("label") for c in report.get("cards") or []]
    assert any("Human API convergence healthy" in str(l) for l in labels)
    assert any("UI ↔ API alignment healthy" in str(l) for l in labels)


def test_human_runtime_replay_artifacts():
    replay = get_human_runtime_replay(session_id="replay-test")
    assert replay.get("ok") is True
    artifacts = replay.get("artifacts") or {}
    assert "human_runtime_state" in artifacts
    assert "living_presence_cycle" in artifacts


def test_contextual_nudge_operational_specificity():
    from aethos_core.human_centered.continuity_memory import seed_default_continuity

    seed_default_continuity(session_id="nudge-test")
    record_focus(session_id="nudge-test", topic="Railway deployment debugging")
    nudge = build_contextual_nudge(session_id="nudge-test")
    text = nudge.get("nudge", "")
    assert "Human API" in text or "404" in text or "mcFetch" in text
    assert "Would you like" in text or "Would you like me to" in text
    assert "Governed assistance" not in text


def test_continue_where_we_left_off_specificity():
    record_conversation_thread(
        session_id="continuity-test",
        topics=["Railway restart verification", "GitHub workflow discovery"],
        unresolved=["deployment evidence reliability"],
    )
    result = resolve_chat_turn("continue where we left off", session_id="continuity-test")
    assert "Railway" in result.reply or "GitHub" in result.reply
    assert "Governed assistance — I recommend" not in result.reply


def test_operational_memory_seeded_on_empty():
    from aethos_core.conversation.operational_memory import load_operational_memory, seed_default_operational_context

    mem = load_operational_memory(session_id="seed-test")
    assert not mem.get("focus_topics")
    seed_default_operational_context(session_id="seed-test")
    mem2 = load_operational_memory(session_id="seed-test")
    assert "Human API" in " ".join(mem2.get("focus_topics") or []) or "Living" in " ".join(mem2.get("focus_topics") or [])


def test_human_integrity_api():
    client = TestClient(app)
    r = client.get("/api/v1/human/integrity")
    assert r.status_code == 200
    assert r.json().get("phase") == "10.1.1"
