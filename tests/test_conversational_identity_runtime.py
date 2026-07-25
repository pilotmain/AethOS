# SPDX-License-Identifier: Apache-2.0
"""Conversational identity runtime tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.continuity_intelligence.conversational_identity_runtime import (
    compose_conversational_identity_reply,
    guard_generative_amnesia,
    is_forbidden_amnesia_reply,
)
from aethos_core.continuity_intelligence.operational_focus_model import clear_focus_for_tests
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_threads_for_tests()
    clear_focus_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    clear_focus_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _seed_speakglobal(session_id: str) -> None:
    preflight = authority.create_job(
        title="Railway restart speakglobal-ai",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "target": {"project_name": "adequate-luck", "environment": "production", "service_name": "speakglobal-ai"},
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="Mutation execution",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "execution_state": "execution_failed",
            "failure_truth": {
                "failure_reason": "The restart failed before Railway mutation because the stored source binding still points to **rayameresa/speakglobal-ai**.",
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_execution_job(job=job_store.get(execution.id))
    authority.create_job(
        title="Mutation execution pilotos",
        job_type="mutation_execution",
        params={"provider": "railway", "operation_type": "restart", "target_name": "pilotos-api"},
        source="test",
        session_id=session_id,
        auto_run=False,
    )


def test_what_were_we_doing_last_hour():
    _seed_speakglobal("hour-recall")
    reply = compose_conversational_identity_reply("Do you remember what we were doing last one hour?", session_id="hour-recall")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "continuity_session_recall"
    assert "don't have memory" not in body.lower()
    assert "speakglobal-ai" in body or "operational" in body.lower()


def test_what_were_we_doing_with_speakglobal():
    _seed_speakglobal("service-recall")
    reply = compose_conversational_identity_reply("what were we doing with speakglobal-ai?", session_id="service-recall")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "continuity_service_recall"
    assert "speakglobal-ai" in body
    assert "pilotos-api" not in body.split("speakglobal-ai")[0]


def test_generic_amnesia_blocked():
    assert is_forbidden_amnesia_reply("I don't have memory of our previous conversations.")
    replacement = guard_generative_amnesia(
        user_text="Do you remember what we were doing last one hour?",
        session_id="amnesia-block",
        reply="I don't have memory of our previous conversations.",
        intent="generative_answer",
    )
    assert replacement is None or "don't have memory" not in replacement[0].lower()


def test_api_continuity_recall_no_amnesia():
    from aethos_core.api.main import app

    _seed_speakglobal("api-recall")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "what were we doing with speakglobal-ai?", "session_id": "api-recall"},
    )
    body = response.json()
    assert "speakglobal-ai" in body["reply"]
    assert "don't have memory" not in body["reply"].lower()
