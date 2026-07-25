# SPDX-License-Identifier: Apache-2.0
"""Conversational memory routing tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.conversation.provider_memory.conversational_memory_router import compose_provider_followup_reply
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.provider_topology.followup_lock import compose_thread_continuation_reply
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_threads_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _seed_thread(session_id: str = "routing-test") -> None:
    preflight = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "target": {
                "project_name": "pilotos",
                "environment": "production",
                "service_name": "pilotos-api",
                "resolved": True,
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "execution_state": "execution_stabilizing",
            "restart_verification_state": "restart_requested",
            "mutation_execution_approved_at_iso": "2026-05-20T10:00:00+00:00",
            "provider_evidence_bundle": {
                "approved_at": "2026-05-20T10:00:00+00:00",
                "logs_excerpt": [
                    {"timestamp": "2026-05-20T10:01:00+00:00", "level": "INFO", "message": "Application startup complete."},
                ],
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    sync_thread_from_execution_job(job=stored)


def test_actionable_followup_runs_before_passive_thread_lock():
    _seed_thread("route-lock")
    passive = compose_thread_continuation_reply("did the restart actually happened?", session_id="route-lock")
    assert passive is None
    reply = compose_provider_followup_reply("did the restart actually happened?", session_id="route-lock")
    assert reply is not None
    body, intent, _meta = reply
    assert "continuing the active" not in body.lower()
    assert "Tell me what you need" not in body
    assert intent.startswith("actionable_") or intent.startswith("provider_followup_")


def test_no_generic_fallback_for_clear_followup():
    from aethos_core.api.main import app

    _seed_thread("route-api")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "did the restart actually happened?", "session_id": "route-api"},
    )
    body = response.json()
    assert "Tell me what you need" not in body["reply"]
    assert "continuing the active" not in body["reply"].lower()
    assert "Conclusion" in body["reply"]


def test_mutation_preflight_does_not_block_followup():
    from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply

    _seed_thread("route-preflight")
    blocked = create_mutation_preflight_job_reply("did the restart actually happened?", session_id="route-preflight")
    assert blocked is None


def test_passive_lock_only_for_unclassified_continuation_prompt():
    _seed_thread("route-passive")
    reply = compose_thread_continuation_reply("what do you need from me?", session_id="route-passive")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "operational_thread_continuation"
