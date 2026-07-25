# SPDX-License-Identifier: Apache-2.0
"""Retry after binding update chat routing tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, get_binding, save_binding
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store
from aethos_core.task_frame.pending_action import get_pending_action


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


def _seed(session_id: str) -> None:
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


def test_binding_update_then_please_do_creates_preflight(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.provider_topology import github_access_verifier

    monkeypatch.setattr(github_access_verifier, "list_accessible_github_repos", lambda: ["pilotmain/speakglobal-ai"])
    _seed("retry-flow")
    client = TestClient(app)
    client.post(
        "/api/v1/chat",
        json={"message": "use pilotmain/speakglobal-ai instead", "session_id": "retry-flow"},
    )
    assert get_pending_action(session_id="retry-flow") is not None
    response = client.post(
        "/api/v1/chat",
        json={"message": "please do", "session_id": "retry-flow"},
    )
    body = response.json()
    assert body.get("intent") == "pending_action_preflight_created"
    assert "speakglobal-ai" in body["reply"]
    assert "pilotmain/speakglobal-ai" in body["reply"]
    assert "I'm ready to help" not in body["reply"]


def test_failed_retry_why_did_it_fail_shows_current_failure(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.provider_topology.failure_truth_expander import expand_failure_truth

    _seed("retry-fail")
    job = job_store.list_all()[-1]
    job.params["failure_truth"] = expand_failure_truth(job)
    job.params["failure_reason"] = job.params["failure_truth"]
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "why did it fail?", "session_id": "retry-fail"},
    )
    body = response.json()
    assert body.get("intent") in {"operational_thread_why_failed", "operational_thread_followup"}
    assert "Failure stage" in body["reply"] or "failure_stage" in body["reply"].lower() or "Provider error" in body["reply"]


def test_restart_without_source_binding_not_blocked(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.provider_topology.topology_memory import clear_topology_for_tests

    clear_topology_for_tests()
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "restart railway speakglobal-ai service", "session_id": "restart-no-bind"},
    )
    body = response.json()
    assert body.get("intent") != "provider_binding_mismatch"
    assert "provider source mismatch" not in body["reply"].lower()
