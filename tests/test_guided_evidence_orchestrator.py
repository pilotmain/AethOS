# SPDX-License-Identifier: Apache-2.0
"""Guided evidence collection execution tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome, reset_repair_memory_for_tests, save_repair_attempt
from aethos_core.runtime.jobs import job_store
from aethos_core.world_model.guided_evidence_orchestrator import (
    execute_guided_evidence_collection,
    should_execute_guided_evidence,
    try_enrich_strategy_with_guided_evidence,
)
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.investigation_strategy_router import compose_investigation_strategy_route_reply
from aethos_core.world_model.world_state_store import clear_world_model_for_tests, load_investigation_state, save_investigation_state


@pytest.fixture(autouse=True)
def _clean():
    reset_repair_memory_for_tests()
    clear_world_model_for_tests()
    job_store.clear_for_tests()
    yield
    reset_repair_memory_for_tests()
    clear_world_model_for_tests()
    job_store.clear_for_tests()


def _mongo_row() -> dict:
    return {
        "service": "MongoDB",
        "project": "pilotcore-sales-engine",
        "environment": "production",
        "status": "failed",
        "health": "failed",
        "deployment_state": "failed",
        "service_id": "svc-mongo",
    }


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
    row = _mongo_row()
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
        next_best_action_key="refresh_events_and_fetch_failure_window_logs",
    )
    save_investigation_state(state)
    return state


def _mock_railway_evidence(*, log_message: str = "Fatal assertion error during startup"):
    logs_payload = {
        "ok": True,
        "logs": [{"timestamp": "2026-05-20T01:00:00Z", "message": log_message}],
        "sources_checked": ["deployment_logs"],
        "errors": [],
        "all_sources_failed": False,
    }
    events_payload = {
        "ok": True,
        "events": [
            {
                "id": "dep-1",
                "state": "FAILED",
                "created_at": "2026-05-20T00:59:00Z",
                "message": "Deployment dep-1 state=FAILED",
                "error_message": "container exited with code 1",
            }
        ],
    }
    return patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value=logs_payload,
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value=events_payload,
    ), patch(
        "aethos_core.world_model.guided_evidence_orchestrator.can_execute_readonly_guided_evidence",
        return_value=(True, ""),
    )


def test_should_execute_guided_evidence_after_failed_restart() -> None:
    outcome = _seed_failed_repair_outcome(session_id="guided-eligible")
    assert should_execute_guided_evidence(state=None, outcome=outcome) is True


def test_should_not_execute_guided_evidence_after_successful_restart() -> None:
    outcome = RepairAttemptOutcome(
        target="pilotcore-sales-engine / production / MongoDB",
        operation="restart",
        attempted_at="2026-05-20T12:00:00+00:00",
        result="recovered",
        health_after="healthy",
        helped=True,
        provider="railway",
        service="MongoDB",
        session_id="guided-helped",
    )
    assert should_execute_guided_evidence(state=None, outcome=outcome) is False


def test_execute_guided_evidence_updates_investigation_state() -> None:
    session_id = "guided-state-update"
    outcome = _seed_failed_repair_outcome(session_id=session_id)
    state = _seed_investigation_state(session_id=session_id)
    logs_patch, events_patch, cred_patch = _mock_railway_evidence()
    with logs_patch, events_patch, cred_patch:
        result = execute_guided_evidence_collection(session_id=session_id, state=state, outcome=outcome)
    assert result.ok is True
    assert result.evidence is not None
    assert result.investigation_state is not None
    stored = load_investigation_state(session_id=session_id, target=state.target)
    assert stored is not None
    assert any(entry.get("kind") == "guided_evidence_collection" for entry in stored.timeline)


def test_strategy_question_executes_guided_evidence_and_returns_findings() -> None:
    session_id = "guided-strategy-reply"
    _seed_failed_repair_outcome(session_id=session_id)
    _seed_investigation_state(session_id=session_id)
    logs_patch, events_patch, cred_patch = _mock_railway_evidence()
    with logs_patch, events_patch, cred_patch:
        routed = compose_investigation_strategy_route_reply("what should we do next?", session_id=session_id)
    assert routed is not None
    body, intent, meta = routed
    assert intent == "investigation_strategy_regressed"
    assert meta.get("guided_evidence_executed") == "true"
    assert "gathering deeper evidence" in body.lower()
    assert "Findings:" in body
    assert "avoid another restart" in body.lower()
    assert "No mutation has been performed." in body
    assert "Fetch full logs around the latest failed deployment window" not in body


def test_strategy_question_does_not_create_mutation_job() -> None:
    session_id = "guided-no-mutation"
    _seed_failed_repair_outcome(session_id=session_id)
    _seed_investigation_state(session_id=session_id)
    logs_patch, events_patch, cred_patch = _mock_railway_evidence()
    with logs_patch, events_patch, cred_patch:
        resolve_chat_turn("what we should do next?", session_id=session_id)
    jobs = [job for job in job_store.list_all() if job.session_id == session_id]
    assert not any(job.job_type in {"mutation_execution", "mutation_preflight"} for job in jobs)


def test_guided_evidence_skips_when_credentials_missing() -> None:
    session_id = "guided-no-creds"
    outcome = _seed_failed_repair_outcome(session_id=session_id)
    state = _seed_investigation_state(session_id=session_id)
    base = "The **MongoDB** restart did not resolve the failure, so I would avoid another restart right now."
    with patch(
        "aethos_core.world_model.guided_evidence_orchestrator.can_execute_readonly_guided_evidence",
        return_value=(False, "Railway read credentials are not configured."),
    ):
        enriched, meta = try_enrich_strategy_with_guided_evidence(
            base,
            session_id=session_id,
            state=state,
            outcome=outcome,
            opener_lines=[base],
        )
    assert meta == {}
    assert "Read-only evidence collection skipped" in enriched
