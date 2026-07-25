# SPDX-License-Identifier: Apache-2.0
"""Provider follow-up runtime tests."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.conversation.provider_memory.provider_followup_runtime import handle_provider_followup
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, get_active_thread
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
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


def _seed_railway_thread(session_id: str = "runtime-railway") -> None:
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
            "target": {
                "project_name": "pilotos",
                "environment": "production",
                "service_name": "pilotos-api",
            },
            "mutation_execution_approved_at_iso": "2026-05-20T10:00:00+00:00",
            "execution_state": "execution_stabilizing",
            "restart_verification_state": "restart_requested",
            "provider_evidence_bundle": {
                "approved_at": "2026-05-20T10:00:00+00:00",
                "logs_excerpt": [
                    {"timestamp": "2026-05-20T10:05:00+00:00", "level": "INFO", "message": "Application startup complete."},
                    {"timestamp": "2026-05-20T10:04:30+00:00", "level": "INFO", "message": "Booting worker"},
                    {"timestamp": "2026-05-20T10:04:00+00:00", "level": "INFO", "message": "Starting container"},
                    {"timestamp": "2026-05-20T10:03:30+00:00", "level": "WARN", "message": "Health check pending"},
                    {"timestamp": "2026-05-20T10:03:00+00:00", "level": "INFO", "message": "Restart requested"},
                    {"timestamp": "2026-05-20T10:02:00+00:00", "level": "ERROR", "message": "Old error line"},
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


def test_active_railway_thread_verify_phrase():
    _seed_railway_thread("verify-runtime")
    result = handle_provider_followup(session_id="verify-runtime", user_text="did the restart actually happened?")
    assert result is not None
    assert "pilotos-api" in result.body
    assert "Conclusion" in result.body
    assert "Tell me what you need" not in result.body


def test_active_railway_thread_top_5_logs():
    _seed_railway_thread("logs-runtime")
    result = handle_provider_followup(
        session_id="logs-runtime",
        user_text="i want you to check if actually restart happend and give me top 5 latest logs",
    )
    assert result is not None
    assert "Latest 5 logs" in result.body
    assert "Conclusion" in result.body
    assert len(result.logs) <= 5


def test_active_thread_unsupported_provider_honest_gap():
    thread = OperationalThreadState(
        session_id="vercel-gap",
        provider="vercel",
        project="demo",
        service="demo-app",
        operation="redeploy",
        status="stabilizing",
    )
    from aethos_core.operational_thread_memory.thread_persistence import save_thread_state

    save_thread_state(thread)
    result = handle_provider_followup(session_id="vercel-gap", user_text="did the redeploy actually happen?")
    assert result is not None
    assert "not implemented yet" in result.body.lower() or "not available" in result.body.lower()


def test_no_active_thread_returns_none():
    result = handle_provider_followup(session_id="missing-thread", user_text="did the restart actually happened?")
    assert result is None


def test_followup_persists_thread_memory():
    _seed_railway_thread("memory-runtime")
    handle_provider_followup(session_id="memory-runtime", user_text="did the restart actually happened?")
    thread = get_active_thread(session_id="memory-runtime")
    assert thread is not None
    assert thread.last_evidence
    assert thread.approved_at == "2026-05-20T10:00:00+00:00"
