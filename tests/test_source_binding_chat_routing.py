# SPDX-License-Identifier: Apache-2.0
"""Source binding chat routing tests."""

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


def test_repo_correction_routes_before_preflight(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.provider_topology import github_access_verifier

    monkeypatch.setattr(
        github_access_verifier,
        "list_accessible_github_repos",
        lambda: ["pilotmain/speakglobal-ai"],
    )
    _seed("chat-binding")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "use https://github.com/pilotmain/speakglobal-ai/ instead",
            "session_id": "chat-binding",
        },
    )
    body = response.json()
    assert body.get("intent") in {
        "source_binding_correction",
        "source_binding_confirmation",
        "source_binding_updated",
    }
    assert "pilotmain/speakglobal-ai" in body["reply"]
    assert "Vercel restart mutation preflight" not in body["reply"]


def test_restart_repo_not_parsed_as_railway_service(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.provider_topology import github_access_verifier

    monkeypatch.setattr(
        github_access_verifier,
        "list_accessible_github_repos",
        lambda: ["pilotmain/speakglobal-ai"],
    )
    _seed("chat-restart-repo")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "restart railway pilotmain/speakglobal-ai service",
            "session_id": "chat-restart-repo",
        },
    )
    body = response.json()
    assert body.get("intent") == "source_binding_correction"
    assert "GitHub repository" in body["reply"]
    assert "Could not confirm a Railway service matching **pilotmain**" not in body["reply"]


def test_confirmation_updates_binding(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.provider_topology import github_access_verifier
    from aethos_core.provider_topology.topology_memory import get_binding

    monkeypatch.setattr(
        github_access_verifier,
        "list_accessible_github_repos",
        lambda: ["pilotmain/speakglobal-ai"],
    )
    _seed("chat-confirm")
    client = TestClient(app)
    client.post(
        "/api/v1/chat",
        json={"message": "can you check https://github.com/pilotmain/speakglobal-ai/", "session_id": "chat-confirm"},
    )
    response = client.post(
        "/api/v1/chat",
        json={"message": "yes update it", "session_id": "chat-confirm"},
    )
    body = response.json()
    assert body.get("intent") == "source_binding_updated"
    binding = get_binding(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
    )
    assert binding is not None
    assert binding.github_repo == "pilotmain/speakglobal-ai"
