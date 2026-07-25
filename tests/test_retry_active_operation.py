# SPDX-License-Identifier: Apache-2.0
"""Retry active operation execution tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, save_binding
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store
from aethos_core.task_frame.pending_action import get_pending_action, offer_retry_preflight_action
from aethos_core.task_frame.retry_active_operation import compose_retry_active_operation_reply, is_retry_intent


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


def _seed_failed_thread(session_id: str = "retry-active", *, github_repo: str = "pilotmain/speakglobal-ai") -> None:
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            service_id="svc-speakglobal",
            github_repo=github_repo,
            source_verified=github_repo == "pilotmain/speakglobal-ai",
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
                "service_id": "svc-speakglobal",
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
            "target_name": "speakglobal-ai",
            "target": {
                "project_name": "adequate-luck",
                "environment": "production",
                "service_name": "speakglobal-ai",
                "service_id": "svc-speakglobal",
            },
            "executed": False,
            "execution_state": "execution_failed",
            "error": "No GitHub installation found for repo: rayameresa/speakglobal-ai",
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


def test_can_you_retry_to_restart_now_creates_preflight():
    _seed_failed_thread("retry-phrase")
    reply = compose_retry_active_operation_reply(
        "can you retry to restart now?",
        session_id="retry-phrase",
    )
    assert reply is not None
    body, intent, meta = reply
    assert intent == "pending_action_preflight_created"
    assert "speakglobal-ai" in body
    assert "I'm ready to help" not in body
    assert meta.get("proposed_job_id")


def test_restart_inside_failed_active_thread_retries_same_operation():
    _seed_failed_thread("restart-only")
    assert is_retry_intent("restart", session_id="restart-only") is True
    reply = compose_retry_active_operation_reply("restart", session_id="restart-only")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "pending_action_preflight_created"
    assert "restart" in body.lower()


def test_please_do_after_binding_update_creates_preflight(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.provider_topology import github_access_verifier

    monkeypatch.setattr(github_access_verifier, "list_accessible_github_repos", lambda: ["pilotmain/speakglobal-ai"])
    _seed_failed_thread("please-do-retry", github_repo="rayameresa/speakglobal-ai")
    client = TestClient(app)
    client.post(
        "/api/v1/chat",
        json={"message": "use pilotmain/speakglobal-ai instead", "session_id": "please-do-retry"},
    )
    assert get_pending_action(session_id="please-do-retry") is not None
    response = client.post(
        "/api/v1/chat",
        json={"message": "please do", "session_id": "please-do-retry"},
    )
    body = response.json()
    assert body.get("intent") == "pending_action_preflight_created"
    assert "I'm ready to help" not in body["reply"]


def test_generic_fallback_not_used_for_retry():
    from aethos_core.api.main import app

    _seed_failed_thread("no-generic")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "can you retry to restart now?", "session_id": "no-generic"},
    )
    body = response.json()
    assert body.get("intent") == "pending_action_preflight_created"
    assert "I'm ready to help" not in body["reply"]


def test_unrelated_provider_preflight_not_created():
    from aethos_core.api.main import app

    _seed_failed_thread("no-vercel")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "can you retry to restart now?", "session_id": "no-vercel"},
    )
    body = response.json()
    assert "Vercel restart mutation preflight" not in body["reply"]
    assert body.get("intent") == "pending_action_preflight_created"
