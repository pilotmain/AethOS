# SPDX-License-Identifier: Apache-2.0
"""Chat routing for repository transfer reconciliation."""

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
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    sync_thread_from_execution_job(job=stored)


def test_reconcile_repo_transfer_chat(monkeypatch):
    from aethos_core.api.main import app
    from aethos_core.provider_topology import github_access_verifier, repo_reconciliation

    monkeypatch.setattr(github_access_verifier, "list_accessible_github_repos", lambda: ["pilotmain/speakglobal-ai"])
    monkeypatch.setattr(
        repo_reconciliation,
        "read_local_git_remote",
        lambda path, remote_name="origin": repo_reconciliation.RepoRemoteInfo(
            path=path or "",
            remote_url="git@github.com:pilotmain/speakglobal-ai.git",
            owner_repo="pilotmain/speakglobal-ai",
            ok=True,
            message="local",
        ),
    )
    monkeypatch.setattr(
        repo_reconciliation,
        "read_railway_service_source_metadata",
        lambda **kwargs: repo_reconciliation.RailwaySourceMetadata(
            service_name=kwargs.get("service_name", ""),
            project=kwargs.get("project", ""),
            environment=kwargs.get("environment", "production"),
            linked_repo="rayameresa/speakglobal-ai",
            stale=True,
            message="stale railway",
        ),
    )
    _seed("repo-transfer-chat")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "reconcile source binding after repo moved", "session_id": "repo-transfer-chat"},
    )
    body = response.json()
    assert body.get("intent") in {"repo_reconciliation", "source_binding_correction", "source_binding_updated"}
    assert "pilotmain/speakglobal-ai" in body["reply"]
    assert "Layer checks" in body["reply"] or "layer checks" in body["reply"].lower()
    assert "rayameresa/speakglobal-ai" in body["reply"]
