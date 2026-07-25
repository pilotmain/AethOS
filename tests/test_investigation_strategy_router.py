# SPDX-License-Identifier: Apache-2.0
"""Investigation strategy router tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.deterministic import match_project_template, try_partial_template
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.provider_memory.conversational_memory_router import compose_provider_followup_reply
from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import reset_operation_state_store_for_tests
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.post_mutation_verification.verification_intent_router import reset_pending_verification_for_tests
from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome, reset_repair_memory_for_tests, save_repair_attempt
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.investigation_strategy_router import (
    compose_investigation_strategy_route_reply,
    is_investigation_strategy_question,
    route_investigation_strategy_question,
)
from aethos_core.world_model.world_state_store import clear_world_model_for_tests, save_investigation_state


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    reset_repair_memory_for_tests()
    reset_operation_state_store_for_tests()
    reset_global_lifecycle_index_for_tests()
    reset_pending_verification_for_tests()
    clear_world_model_for_tests()
    from aethos_core.runtime.jobs import job_store

    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    reset_repair_memory_for_tests()
    reset_operation_state_store_for_tests()
    reset_global_lifecycle_index_for_tests()
    reset_pending_verification_for_tests()
    clear_world_model_for_tests()
    job_store.clear_for_tests()


def _seed_failed_repair_outcome(*, session_id: str) -> RepairAttemptOutcome:
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


def _seed_investigation_state(*, session_id: str) -> InvestigationState:
    row = {
        "service": "MongoDB",
        "project": "pilotcore-sales-engine",
        "environment": "production",
    }
    state = InvestigationState(
        target=target_label_from_row(row),
        session_id=session_id,
        service="MongoDB",
        project="pilotcore-sales-engine",
        environment="production",
        confidence_score=0.55,
        confidence_label="bounded",
        active_investigation=True,
        evidence=["failed_runtime_status", "fresh_wiredtiger_logs", "stale_service_events"],
        next_best_action="Refresh Railway service events and fetch logs around the latest failed deployment window.",
    )
    save_investigation_state(state)
    return state


def _seed_active_railway_thread(session_id: str) -> None:
    from aethos_core.runtime.authority import authority
    from aethos_core.runtime.jobs import job_store

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


def test_is_investigation_strategy_question_variants() -> None:
    assert is_investigation_strategy_question("what we should do next?")
    assert is_investigation_strategy_question("what should we do next?")
    assert is_investigation_strategy_question("what next")
    assert is_investigation_strategy_question("how should we continue")
    assert not is_investigation_strategy_question("did restart help?")


def test_what_we_should_do_next_returns_operational_strategy() -> None:
    session_id = "strategy-we-next"
    _seed_failed_repair_outcome(session_id=session_id)
    _seed_investigation_state(session_id=session_id)

    with patch(
        "aethos_core.world_model.guided_evidence_orchestrator.can_execute_readonly_guided_evidence",
        return_value=(True, ""),
    ), patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={
            "ok": True,
            "logs": [{"timestamp": "2026-05-20T01:00:00Z", "message": "WiredTiger recovery message"}],
            "sources_checked": ["deployment_logs"],
            "errors": [],
        },
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={
            "ok": True,
            "events": [{"id": "dep-1", "state": "FAILED", "created_at": "2026-05-20T00:59:00Z", "message": "FAILED"}],
        },
    ):
        reply = compose_investigation_strategy_route_reply("what we should do next?", session_id=session_id)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "investigation_strategy_regressed"
    assert meta.get("route_id") == "investigation_strategy"
    assert meta.get("guided_evidence_executed") == "true"
    assert "avoid another restart" in body.lower()
    assert "gathering deeper evidence" in body.lower()
    assert "Findings:" in body
    assert "MongoDB" in body


def test_what_next_returns_operational_strategy() -> None:
    session_id = "strategy-what-next"
    _seed_failed_repair_outcome(session_id=session_id)

    with patch(
        "aethos_core.world_model.guided_evidence_orchestrator.can_execute_readonly_guided_evidence",
        return_value=(True, ""),
    ), patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": ["logs unavailable"]},
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": False, "events": []},
    ):
        result = route_investigation_strategy_question("what next", session_id=session_id)
    assert result is not None
    assert "restart did not resolve" in result.reply.lower() or "avoid another restart" in result.reply.lower()
    assert result.meta.get("route_id") == "investigation_strategy"
    assert result.meta.get("guided_evidence_executed") == "true"


def test_how_should_we_continue_returns_operational_strategy() -> None:
    session_id = "strategy-continue"
    _seed_failed_repair_outcome(session_id=session_id)
    _seed_investigation_state(session_id=session_id)

    with patch(
        "aethos_core.world_model.guided_evidence_orchestrator.can_execute_readonly_guided_evidence",
        return_value=(True, ""),
    ), patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={
            "ok": True,
            "logs": [{"timestamp": "2026-05-20T01:00:00Z", "message": "connection refused"}],
            "sources_checked": ["deployment_logs"],
            "errors": [],
        },
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": True, "events": []},
    ):
        reply = compose_investigation_strategy_route_reply("how should we continue?", session_id=session_id)
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "investigation_strategy_regressed"
    assert "inspecting Railway service events" in body


def test_restart_regression_suppresses_restart_recommendation() -> None:
    session_id = "strategy-no-restart"
    _seed_failed_repair_outcome(session_id=session_id)

    with patch(
        "aethos_core.world_model.guided_evidence_orchestrator.can_execute_readonly_guided_evidence",
        return_value=(True, ""),
    ), patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": []},
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": False, "events": []},
    ):
        reply = compose_investigation_strategy_route_reply("what should we do next?", session_id=session_id)
    assert reply is not None
    body, _intent, _meta = reply
    assert "would not recommend another restart or redeploy" in body.lower()
    assert "restart" in body.lower()


def test_generic_assistant_fallback_blocked_during_active_investigation() -> None:
    session_id = "strategy-live"
    _seed_active_railway_thread(session_id)
    _seed_failed_repair_outcome(session_id=session_id)
    _seed_investigation_state(session_id=session_id)

    assert match_project_template("what we should do next?", session_id=session_id) is None
    assert try_partial_template("what we should do next?", session_id=session_id) is None
    assert compose_provider_followup_reply("what we should do next?", session_id=session_id) is None

    with patch(
        "aethos_core.world_model.guided_evidence_orchestrator.can_execute_readonly_guided_evidence",
        return_value=(True, ""),
    ), patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": []},
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": False, "events": []},
    ):
        result = resolve_chat_turn("what we should do next?", session_id=session_id)
    assert result.meta.get("route_id") == "investigation_strategy"
    assert "Phase 2" not in result.reply
    assert "Tell me what you need" not in result.reply
    assert "avoid another restart" in result.reply.lower()


def test_no_investigation_context_returns_bounded_clarification() -> None:
    reply = compose_investigation_strategy_route_reply("what should we do next?", session_id="strategy-empty")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "investigation_strategy_clarification"
    assert meta.get("investigation_continuity") == "false"
    assert "which service failure" in body.lower()
    assert "verify health" in body.lower()
