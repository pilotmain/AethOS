# SPDX-License-Identifier: Apache-2.0
"""Provider execution chat truth tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clear_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    job_store.clear_for_tests()


def _seed_execution(session_id: str = "provider-chat") -> str:
    job = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "atlas-trader api",
            "executed": True,
            "restart_command_submitted": True,
            "provider_evidence_bundle": {
                "command": "railway restart --service 'atlas-trader api' --yes --json",
                "command_submitted": True,
                "evidence": {"log_activity_after_approval": True, "health_confirmed": True},
                "verification": {"status": "verified_restart", "verified": True},
                "logs_excerpt": [{"message": "Server listening on port 8080", "timestamp": "2026-01-15T12:05:00+00:00"}],
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


def test_check_logs_intent():
    from aethos_core.api.main import app

    _seed_execution()
    client = TestClient(app)
    response = client.post("/api/v1/chat", json={"message": "check logs", "session_id": "provider-chat"})
    body = response.json()
    assert body.get("intent") == "provider_execution_logs"
    assert "logs" in body["reply"].lower()


def test_why_did_it_fail_intent():
    from aethos_core.api.main import app

    job_id = _seed_execution(session_id="provider-chat-fail")
    job = job_store.get(job_id)
    assert job is not None
    job.params["provider_evidence_bundle"] = {
        "logs_excerpt": [{"message": "DATABASE_URL is missing", "timestamp": "2026-01-15T12:00:00+00:00"}],
    }
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "why did it fail?", "session_id": "provider-chat-fail"},
    )
    body = response.json()
    assert body.get("intent") == "provider_execution_diagnosis"


def test_fix_it_requires_approval():
    from aethos_core.api.main import app

    job_id = _seed_execution(session_id="provider-chat-fix")
    job = job_store.get(job_id)
    assert job is not None
    job.params["provider_evidence_bundle"] = {
        "logs_excerpt": [{"message": "Missing API_KEY env var", "timestamp": "2026-01-15T12:00:00+00:00"}],
    }
    client = TestClient(app)
    response = client.post("/api/v1/chat", json={"message": "fix it", "session_id": "provider-chat-fix"})
    body = response.json()
    assert body.get("intent") == "provider_execution_fix_plan"
    assert "approval" in body["reply"].lower()


def test_redeploy_points_to_preflight():
    from aethos_core.api.main import app

    _seed_execution(session_id="provider-chat-redeploy")
    client = TestClient(app)
    response = client.post("/api/v1/chat", json={"message": "redeploy it", "session_id": "provider-chat-redeploy"})
    body = response.json()
    assert body.get("intent") == "provider_execution_redeploy"
    assert "preflight" in body["reply"].lower() or "approve" in body["reply"].lower()
