# SPDX-License-Identifier: Apache-2.0
"""Operational thread memory — post-mutation follow-up continuity."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.mutation_thread_memory import (
    sync_thread_from_execution_job,
    sync_thread_from_preflight,
)
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.operational_thread_memory.actionable_followup import compose_actionable_followup_reply
from aethos_core.operational_thread_memory.thread_reply_composer import compose_operational_thread_followup
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.operational_thread_memory.thread_persistence import save_thread_state
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


def _seed_thread(*, session_id: str = "thread-test", status: str = "restart_unverified") -> str:
    preflight = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "influencer-crm",
            "target": {
                "project_name": "influencer-crm",
                "environment": "production",
                "service_name": "influencer-crm",
                "resolved": True,
            },
            "user_request": "restart railway influencer-crm service",
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight, user_request="restart railway influencer-crm service")

    execution = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "influencer-crm",
            "target": {
                "project_name": "influencer-crm",
                "environment": "production",
                "service_name": "influencer-crm",
            },
            "preflight_job_id": preflight.id,
            "executed": True,
            "restart_command_submitted": True,
            "restart_verification_state": status,
            "execution_state": "execution_stabilizing",
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    sync_thread_from_execution_job(job=stored)
    return execution.id


def test_vague_check_resolves_latest_railway_thread():
    job_id = _seed_thread(session_id="thread-check")
    reply = compose_actionable_followup_reply("can you check and report back?", session_id="thread-check")
    assert reply is not None
    body, intent, meta = reply
    assert intent in {"actionable_check_status", "provider_followup_get_status"}
    assert "influencer-crm" in body
    assert "restart" in body.lower() or "Railway" in body
    assert job_id in body or meta.get("execution_job_id") == job_id
    assert "don't have enough context" not in body.lower()


def test_thread_recall_returns_active_mutation_context():
    _seed_thread(session_id="thread-recall")
    reply = compose_operational_thread_followup(
        "what were we talking about few seconds before?",
        session_id="thread-recall",
    )
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "operational_thread_recall"
    assert "influencer-crm" in body
    assert "restart" in body.lower()
    assert "verify" in body.lower() or "evidence" in body.lower()


def test_failed_speakglobal_restart_exposes_failure_reason():
    execution = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "target": {"project_name": "speakglobal", "environment": "production", "service_name": "speakglobal-ai"},
            "executed": False,
            "execution_state": "execution_failed",
            "mutation_execution": {
                "execution_state": "execution_failed",
                "provider_result": {"detail": "Service ID svc-wrong not found in project speakglobal"},
            },
        },
        source="test",
        session_id="thread-speak",
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    sync_thread_from_execution_job(job=stored)

    reply = compose_operational_thread_followup("why did speakglobal-ai fail?", session_id="thread-speak")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "operational_thread_why_failed"
    assert "speakglobal-ai" in body
    assert "Service ID" in body or "not found" in body
    assert "execution failed" not in body.lower() or "Reason:" in body


def test_no_generic_fallback_when_active_thread_exists():
    from aethos_core.api.main import app

    _seed_thread(session_id="thread-api")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "can you check and report back?", "session_id": "thread-api"},
    )
    body = response.json()
    assert body.get("intent") == "actionable_check_status"
    assert "influencer-crm" in body["reply"]
    assert "don't have enough context" not in body["reply"].lower()
    assert "don't have context" not in body["reply"].lower()


def test_stale_thread_returns_bounded_uncertainty():
    expired = OperationalThreadState(
        session_id="thread-stale",
        provider="railway",
        project="influencer-crm",
        environment="production",
        service="influencer-crm",
        operation="restart",
        status="restart_unverified",
        expires_at=(datetime.now(UTC) - timedelta(hours=1)).isoformat(),
    )
    save_thread_state(expired)

    reply = compose_operational_thread_followup("can you check?", session_id="thread-stale")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "operational_thread_stale"
    assert "expired" in body.lower() or "don't have an active operational mutation thread" in body.lower()
    assert "don't have enough context" not in body.lower()
