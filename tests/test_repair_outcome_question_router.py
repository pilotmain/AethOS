# SPDX-License-Identifier: Apache-2.0
"""Repair outcome question routing tests."""

from __future__ import annotations

import pytest

from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.provider_memory.conversational_memory_router import compose_provider_followup_reply
from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import reset_operation_state_store_for_tests
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.post_mutation_verification.verification_intent_router import reset_pending_verification_for_tests
from aethos_core.provider_topology.followup_lock import compose_thread_continuation_reply
from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome, reset_repair_memory_for_tests, save_repair_attempt
from aethos_core.repair_memory.repair_outcome_router import (
    compose_repair_outcome_route_reply,
    route_repair_outcome_question,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    job_store.clear_for_tests()
    reset_repair_memory_for_tests()
    reset_operation_state_store_for_tests()
    reset_global_lifecycle_index_for_tests()
    reset_pending_verification_for_tests()
    yield
    clear_threads_for_tests()
    job_store.clear_for_tests()
    reset_repair_memory_for_tests()
    reset_operation_state_store_for_tests()
    reset_global_lifecycle_index_for_tests()
    reset_pending_verification_for_tests()


def _seed_active_railway_thread(session_id: str = "repair-outcome-thread") -> None:
    preflight = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "MongoDB",
            "target": {
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
                "service_name": "MongoDB",
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
            "target_name": "MongoDB",
            "execution_state": "execution_stabilizing",
            "restart_verification_state": "verification_failed",
            "restart_service_health": "failed",
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    sync_thread_from_execution_job(job=stored)


def _seed_failed_repair_outcome(*, session_id: str = "repair-outcome-thread") -> RepairAttemptOutcome:
    outcome = RepairAttemptOutcome(
        target="pilotcore-sales-engine / production / MongoDB",
        operation="restart",
        attempted_at="2026-05-20T12:00:00+00:00",
        result="regressed",
        health_after="failed",
        helped=False,
        evidence=["provider command submitted", "health remains failed", "logs after restart low-signal"],
        lesson="Restart did not resolve the **MongoDB** failure.",
        provider="railway",
        project="pilotcore-sales-engine",
        environment="production",
        service="MongoDB",
        session_id=session_id,
        verification_status="regressed",
    )
    return save_repair_attempt(outcome)


def test_did_restart_help_returns_repair_outcome_answer() -> None:
    _seed_failed_repair_outcome()
    reply = compose_repair_outcome_route_reply("did restart help?", session_id="repair-outcome-thread")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "repair_outcome_not_helped"
    assert meta.get("route_id") == "repair_outcome"
    assert "did not appear to help" in body.lower()
    assert "operation: **restart**" in body
    assert "result: **regressed**" in body
    assert "health after: **failed**" in body
    assert "Restart did not resolve" in body


def test_did_it_help_uses_latest_repair_outcome() -> None:
    _seed_failed_repair_outcome()
    reply = route_repair_outcome_question("did it help?", session_id="repair-outcome-thread")
    assert reply is not None
    assert "health after: **failed**" in reply.reply
    assert reply.meta.get("repair_result") == "regressed"


def test_was_restart_useful_returns_repair_outcome_answer() -> None:
    _seed_failed_repair_outcome()
    reply = compose_repair_outcome_route_reply("was restart useful?", session_id="repair-outcome-thread")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "repair_outcome_not_helped"
    assert "avoid another restart" in body.lower()


def test_no_outcome_available_returns_bounded_reply() -> None:
    reply = compose_repair_outcome_route_reply("did restart help?", session_id="repair-outcome-empty")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "repair_outcome_unavailable"
    assert meta.get("repair_outcome_available") == "false"
    assert "not have a recorded repair outcome" in body.lower()
    assert "verify health" in body.lower()


def test_active_railway_thread_does_not_hijack_did_restart_help() -> None:
    _seed_active_railway_thread("repair-outcome-live")
    _seed_failed_repair_outcome(session_id="repair-outcome-live")

    passive = compose_thread_continuation_reply("did restart help?", session_id="repair-outcome-live")
    assert passive is None

    preflight = create_mutation_preflight_job_reply("did restart help?", session_id="repair-outcome-live")
    assert preflight is None

    provider = compose_provider_followup_reply("did restart help?", session_id="repair-outcome-live")
    assert provider is None

    result = resolve_chat_turn("did restart help?", session_id="repair-outcome-live")
    assert "Tell me what you need" not in result.reply
    assert "continuing the active" not in result.reply.lower()
    assert "did not appear to help" in result.reply.lower()
    assert result.meta.get("route_id") == "repair_outcome"
