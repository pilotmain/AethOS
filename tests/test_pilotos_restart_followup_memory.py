# SPDX-License-Identifier: Apache-2.0
"""Pilotos restart follow-up memory end-to-end regression."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, get_active_thread
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


def _seed_pilotos_restart(session_id: str = "pilotos-followup") -> None:
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
            "user_request": "restart the railway pilotos-api",
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
            "target": {
                "project_name": "pilotos",
                "environment": "production",
                "service_name": "pilotos-api",
            },
            "mutation_execution_approved_at_iso": "2026-05-20T11:00:00+00:00",
            "execution_state": "execution_stabilizing",
            "restart_verification_state": "restart_requested",
            "restart_command_submitted": True,
            "provider_evidence_bundle": {
                "approved_at": "2026-05-20T11:00:00+00:00",
                "logs_excerpt": [
                    {"timestamp": "2026-05-20T11:02:00+00:00", "level": "INFO", "message": "Application startup complete."},
                    {"timestamp": "2026-05-20T11:01:45+00:00", "level": "INFO", "message": "Worker booted"},
                    {"timestamp": "2026-05-20T11:01:30+00:00", "level": "INFO", "message": "Container started"},
                    {"timestamp": "2026-05-20T11:01:15+00:00", "level": "WARN", "message": "Waiting for health"},
                    {"timestamp": "2026-05-20T11:01:00+00:00", "level": "INFO", "message": "Restart signal received"},
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


def test_pilotos_restart_followup_flow():
    from aethos_core.api.main import app

    _seed_pilotos_restart("pilotos-e2e")
    client = TestClient(app)

    verify = client.post(
        "/api/v1/chat",
        json={"message": "did the restart actually happened?", "session_id": "pilotos-e2e"},
    ).json()
    assert "Tell me what you need" not in verify["reply"]
    assert "pilotos-api" in verify["reply"]
    assert "Conclusion" in verify["reply"]

    logs = client.post(
        "/api/v1/chat",
        json={
            "message": "i want you to check if actually restart happend and give me top 5 latest logs",
            "session_id": "pilotos-e2e",
        },
    ).json()
    assert "Latest 5 logs" in logs["reply"]
    assert "Conclusion" in logs["reply"]
    assert "Tell me what you need" not in logs["reply"]

    timestamp = client.post(
        "/api/v1/chat",
        json={"message": "tell me the last timestamp after restart?", "session_id": "pilotos-e2e"},
    ).json()
    assert "2026-05-20T11:02:00+00:00" in timestamp["reply"]

    thread = get_active_thread(session_id="pilotos-e2e")
    assert thread is not None
    assert thread.provider == "railway"
    assert thread.service == "pilotos-api"
    assert thread.last_evidence
