# SPDX-License-Identifier: Apache-2.0
"""Chat flows for Railway target resolution and approval blocking."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _mutation_enabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()


def _seed_unresolved_preflight(*, session_id: str = "target-chat") -> str:
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "user_request": "Restart the Railway atlas-trader api service",
            "preflight_status": "needs_information",
            "target_resolved": False,
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    stored.params["mutation_preflight"] = {
        "provider": "railway",
        "operation_type": "restart",
        "preflight_status": "needs_information",
        "target_resolved": False,
    }
    return job.id


def test_restart_railway_resolves_target_and_creates_preflight():
    from aethos_core.api.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "Restart Railway atlas-trader api service", "session_id": "target-chat"},
    )
    body = response.json()
    assert "atlas-trader api" in body["reply"]
    assert "Runtime actions" in body["reply"] or mutation_approval_surface() in body["reply"]
    assert body.get("meta", {}).get("proposed_job_id", "").startswith("job-")


def test_restart_railway_ambiguous_asks_clarification_without_preflight():
    from aethos_core.api.main import app

    client = TestClient(app)
    before = len(job_store.list_all())
    response = client.post(
        "/api/v1/chat",
        json={"message": "Restart Railway", "session_id": "target-chat-ambiguous"},
    )
    body = response.json()
    assert "Which Railway service" in body["reply"]
    assert "No mutation preflight has been created yet" in body["reply"]
    assert body.get("meta", {}).get("proposed_job_id") is None
    assert len(job_store.list_all()) == before


def test_why_cant_approve_explains_unresolved_target():
    from aethos_core.api.main import app

    job_id = _seed_unresolved_preflight()
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": f"why can't i approve {job_id}?", "session_id": "target-chat"},
    )
    body = response.json()
    assert "target is unresolved" in body["reply"].lower()
    assert "atlas-trader api" in body["reply"]
    assert mutation_approval_surface() in body["reply"] or "Runtime actions" in body["reply"]
    assert "No restart has been performed" in body["reply"]


def test_user_target_update_makes_preflight_ready():
    from aethos_core.api.main import app

    _seed_unresolved_preflight(session_id="target-chat-update")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "the target is atlas-trader api", "session_id": "target-chat-update"},
    )
    body = response.json()
    assert body.get("intent") == "mutation_target_update"
    assert "updated the preflight target" in body["reply"].lower()
    assert mutation_approval_surface() in body["reply"] or "Runtime actions" in body["reply"]
