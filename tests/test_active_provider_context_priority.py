# SPDX-License-Identifier: Apache-2.0
"""Active provider context priority for provider-neutral follow-ups."""

from __future__ import annotations

import pytest

from aethos_core.chat.handlers import resolve_handler
from aethos_core.chat.vercel_readonly_prompts import create_vercel_readonly_job_reply
from aethos_core.config import get_settings
from aethos_core.conversation.provider_memory.active_provider_context import (
    block_vercel_inspection_for_active_context,
    resolve_active_provider_context,
)
from aethos_core.conversation.provider_memory.followup_intent_classifier import classify_followup_intent
from aethos_core.conversation.provider_memory.provider_followup_runtime import handle_provider_followup
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, save_thread_state
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.runtime.authority import authority
from aethos_core.runtime.browser_intents import is_vercel_inspection_request
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


def _seed_railway_thread(session_id: str = "ctx-railway") -> None:
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
            "mutation_execution_approved_at_iso": "2026-05-25T01:13:20+00:00",
            "execution_state": "execution_stabilizing",
            "restart_verification_state": "stabilizing",
            "provider_evidence_bundle": {
                "approved_at": "2026-05-25T01:13:20+00:00",
                "logs_excerpt": [
                    {
                        "timestamp": "2026-05-24T23:09:27+00:00",
                        "level": "INFO",
                        "message": "Application startup complete.",
                    }
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


def test_active_railway_thread_check_service_health_routes_railway():
    _seed_railway_thread("health-railway")
    thread = OperationalThreadState(
        session_id="health-railway",
        provider="railway",
        project="pilotos",
        environment="production",
        service="pilotos-api",
        operation="restart",
        status="stabilizing",
    )
    intent = classify_followup_intent("check Service health", thread)
    assert intent is not None
    assert intent.intent == "health_check"

    result = handle_provider_followup(session_id="health-railway", user_text="check Service health")
    assert result is not None
    assert result.provider == "railway"
    assert "pilotos / production / pilotos-api" in result.body
    assert "Vercel" not in result.body


def test_active_railway_thread_blocks_vercel_health_inspection():
    _seed_railway_thread("block-vercel")
    assert block_vercel_inspection_for_active_context("check Service health", session_id="block-vercel")
    assert not is_vercel_inspection_request("check Service health")
    assert create_vercel_readonly_job_reply("check Service health", session_id="block-vercel") is None


def test_explicit_vercel_health_still_routes_vercel():
    _seed_railway_thread("explicit-vercel")
    assert not block_vercel_inspection_for_active_context(
        "check Vercel service health",
        session_id="explicit-vercel",
    )
    assert is_vercel_inspection_request("check Vercel service health")


def test_no_active_provider_ambiguous_health_asks_clarification():
    packed = create_vercel_readonly_job_reply("check service health", session_id="no-context")
    assert packed is not None
    reply, intent, _meta = packed
    assert intent == "health_check_clarification"
    assert "which provider" in reply.lower()


def test_active_railway_thread_top_logs_uses_railway():
    _seed_railway_thread("top-logs-railway")
    result = handle_provider_followup(
        session_id="top-logs-railway",
        user_text="Check top 5 logs for pilotos-api",
    )
    assert result is not None
    assert result.provider == "railway"
    assert "Latest 5 logs" in result.body or "Latest" in result.body


def test_resolve_handler_prefers_railway_health_over_vercel():
    _seed_railway_thread("handler-health")
    packed = resolve_handler("check Service health", session_id="handler-health")
    assert packed is not None
    reply, intent, meta = packed
    assert meta.get("provider") == "railway"
    assert "pilotos-api" in reply
    assert "vercel_readonly" not in intent


def test_resolve_active_provider_context_from_thread():
    save_thread_state(
        OperationalThreadState(
            session_id="ctx-thread",
            provider="railway",
            project="pilotos",
            environment="production",
            service="pilotos-api",
            operation="restart",
            status="stabilizing",
        )
    )
    ctx = resolve_active_provider_context(session_id="ctx-thread", user_text="check service health")
    assert ctx is not None
    assert ctx.provider == "railway"
    assert ctx.service == "pilotos-api"
    assert ctx.source == "active_operational_thread"
