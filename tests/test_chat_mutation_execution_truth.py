# SPDX-License-Identifier: Apache-2.0
"""Chat truth for mutation execution."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.operations.mutations.lifecycle import EXECUTION_FAILED, EXECUTION_STABILIZING
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


def _seed_failed_execution(session_id: str = "exec-truth") -> str:
    job = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "atlas-trader api",
            "mutation_execution_approved": True,
            "executed": False,
            "execution_state": EXECUTION_FAILED,
            "mutation_execution": {
                "provider_result": {"detail": "Railway mutation credentials are not configured."},
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    return job.id


def _seed_requested_execution(session_id: str = "exec-truth") -> str:
    job = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "atlas-trader api",
            "mutation_execution_approved": True,
            "executed": True,
            "provider_mutation_requested": True,
            "execution_state": EXECUTION_STABILIZING,
            "verification_state": "verification_pending",
            "verification_job_id": "job-verify-1",
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    return job.id


def test_did_restart_actually_happen_missing_credentials():
    from aethos_core.api.main import app

    _seed_failed_execution()
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "did the restart actually happen?", "session_id": "exec-truth"},
    )
    body = response.json()
    assert body.get("intent") == "mutation_execution_truth"
    assert "No" in body["reply"]
    assert "credential" in body["reply"].lower()
    assert "No provider mutation was performed" in body["reply"]


def test_did_restart_actually_happen_provider_accepted():
    from aethos_core.api.main import app

    _seed_requested_execution()
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "did the restart actually happen?", "session_id": "exec-truth"},
    )
    body = response.json()
    assert "Railway accepted the restart request" in body["reply"]
    assert "atlas-trader api" in body["reply"]
    assert "verification" in body["reply"].lower()
    assert "Yes" not in body["reply"]


def test_did_restart_actually_happen_unverified_same_deployment():
    from aethos_core.api.main import app

    job = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "atlas-trader api",
            "mutation_execution_approved": True,
            "executed": True,
            "provider_mutation_requested": True,
            "execution_state": "stabilizing",
            "verification_state": "verification_inconclusive",
            "restart_verification_state": "service_online_but_restart_unproven",
            "verified": False,
        },
        source="test",
        session_id="exec-truth-unverified",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")

    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "did the restart actually happen?", "session_id": "exec-truth-unverified"},
    )
    body = response.json()
    assert body.get("intent") == "mutation_execution_truth"
    assert "No" in body["reply"]
    assert "cannot verify" in body["reply"].lower()
    assert "unverified" in body["reply"].lower()


def test_is_job_done_reports_execution_state():
    from aethos_core.api.main import app

    job_id = _seed_requested_execution(session_id="exec-truth-done")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": f"is {job_id} done?", "session_id": "exec-truth-done"},
    )
    body = response.json()
    assert body.get("intent") == "mutation_execution_truth"
    assert job_id in body["reply"]
