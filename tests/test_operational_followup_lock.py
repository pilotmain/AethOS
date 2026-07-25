# SPDX-License-Identifier: Apache-2.0
"""Operational follow-up continuity lock tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.provider_topology.followup_lock import compose_thread_continuation_reply, should_block_unrelated_preflight
from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, save_binding
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_threads_for_tests()
    clear_topology_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    clear_topology_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _seed_railway_thread(session_id: str = "followup-lock") -> None:
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            github_repo="rayameresa/speakglobal-ai",
        )
    )
    preflight = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "target": {
                "project_name": "adequate-luck",
                "environment": "production",
                "service_name": "speakglobal-ai",
                "resolved": True,
            },
            "user_request": "restart railway speakglobal-ai service",
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight, user_request="restart railway speakglobal-ai service")
    execution = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "target": {"project_name": "adequate-luck", "environment": "production", "service_name": "speakglobal-ai"},
            "executed": False,
            "execution_state": "execution_failed",
            "mutation_execution": {"error": "No GitHub installation found for repo: rayameresa/speakglobal-ai"},
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    sync_thread_from_execution_job(job=stored)


def test_followup_stays_on_railway_thread():
    _seed_railway_thread()
    reply = compose_thread_continuation_reply(
        "what do you need from me for you to actually restart speakglobal-ai?",
        session_id="followup-lock",
    )
    assert reply is not None
    body, intent, meta = reply
    assert intent == "operational_thread_continuation"
    assert "Railway" in body
    assert "speakglobal-ai" in body
    assert meta.get("provider") == "railway"


def test_no_unrelated_vercel_preflight_when_thread_locked():
    from aethos_core.api.main import app

    _seed_railway_thread(session_id="followup-api")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "what do you need from me for you to actually restart speakglobal-ai?",
            "session_id": "followup-api",
        },
    )
    body = response.json()
    assert body.get("intent") in {"operational_thread_continuation", "provider_binding_mismatch"}
    assert "Vercel restart mutation preflight" not in body["reply"]
    assert "vercel" not in body["reply"].lower() or "not creating a **vercel**" in body["reply"].lower()


def test_should_block_unrelated_preflight():
    _seed_railway_thread(session_id="block-test")
    assert should_block_unrelated_preflight("what do you need from me?", session_id="block-test") is True


def test_explicit_provider_switch_allowed():
    _seed_railway_thread(session_id="switch-test")
    assert should_block_unrelated_preflight("switch to vercel and restart speakglobal", session_id="switch-test") is False
