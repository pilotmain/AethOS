# SPDX-License-Identifier: Apache-2.0
"""End-to-end speakglobal retry after binding update."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, get_active_thread
from aethos_core.provider_topology.failure_truth_expander import expand_failure_truth
from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, get_binding, save_binding
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


def _seed_initial_failure(session_id: str) -> None:
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            service_id="svc-speakglobal",
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


def test_speakglobal_binding_update_retry_and_failure_truth(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.provider_topology import github_access_verifier

    monkeypatch.setattr(github_access_verifier, "list_accessible_github_repos", lambda: ["pilotmain/speakglobal-ai"])
    session_id = "speakglobal-e2e"
    _seed_initial_failure(session_id)
    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={"message": "use pilotmain/speakglobal-ai instead", "session_id": session_id},
    )
    assert response.status_code == 200
    binding = get_binding(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
    )
    assert binding is not None
    assert binding.github_repo == "pilotmain/speakglobal-ai"
    assert binding.source_verified is True

    retry = client.post(
        "/api/v1/chat",
        json={"message": "can you retry to restart now?", "session_id": session_id},
    )
    retry_body = retry.json()
    assert retry_body.get("intent") == "pending_action_preflight_created"
    assert "speakglobal-ai" in retry_body["reply"]
    assert "rayameresa/speakglobal-ai" not in retry_body["reply"]
    assert "I'm ready to help" not in retry_body["reply"]

    thread = get_active_thread(session_id=session_id)
    assert thread is not None
    assert thread.status == "preflight_created"

    retry_jobs = [
        job
        for job in job_store.list_all()
        if job.job_type == "mutation_preflight"
        and (
            job.params.get("source_binding") == "pilotmain/speakglobal-ai"
            or (job.params.get("source_binding_resolution") or {}).get("github_repo") == "pilotmain/speakglobal-ai"
        )
    ]
    assert retry_jobs, "Expected retry preflight with canonical source binding"
    assert "rayameresa" not in str(retry_jobs[-1].params)

    old_job = job_store.list_all()[1]
    truth = expand_failure_truth(old_job)
    assert truth is not None
    assert truth["source_binding"]["repo"] == "pilotmain/speakglobal-ai"
    assert "rayameresa/speakglobal-ai" not in truth["provider_error"]

    why = client.post(
        "/api/v1/chat",
        json={"message": "why did it fail?", "session_id": session_id},
    )
    why_body = why.json()
    assert why_body.get("intent") in {"operational_thread_why_failed", "operational_thread_followup"}
    assert "rayameresa/speakglobal-ai" not in why_body["reply"]
