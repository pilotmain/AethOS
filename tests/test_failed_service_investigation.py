# SPDX-License-Identifier: Apache-2.0
"""Failed-service investigation routing tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.handlers import resolve_handler
from aethos_core.conversation.provider_memory.conversational_memory_router import is_provider_followup_request
from aethos_core.failed_service_investigation.failed_service_resolver import resolve_failed_service_target
from aethos_core.failed_service_investigation.failed_service_router import compose_failed_service_investigation_reply
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, save_thread_state
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_threads_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_threads_for_tests()


def _rows() -> list[dict]:
    return [
        {"service": "pilotos-api", "project": "pilotos", "environment": "production", "status": "running", "health": "healthy", "service_id": "svc-1"},
        {"service": "pilotcore-finance-engine", "project": "pilotcore-finance-engine", "environment": "production", "status": "failed", "health": "failed", "deployment_state": "failed", "service_id": "svc-pfe"},
        {"service": "MongoDB", "project": "pilotcore-sales-engine", "environment": "production", "status": "failed", "health": "failed", "deployment_state": "failed", "service_id": "svc-mongo"},
        {"service": "worker", "project": "talking-avatar-worker", "environment": "production", "status": "failed", "health": "failed", "deployment_state": "crashed", "service_id": "svc-worker"},
    ]


def _seed_report(session_id: str) -> None:
    rows = _rows()
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={
            "services": rows,
            "counts": {"total": 4, "healthy": 1, "failed": 3, "unknown": 0},
            "failures": rows[1:],
            "unknown": [],
        },
        summary={"total": 4, "healthy": 1, "failed": 3, "unknown": 0},
    )


def _seed_active_thread(session_id: str) -> None:
    save_thread_state(
        OperationalThreadState(
            session_id=session_id,
            provider="railway",
            project="pilotcore-finance-engine",
            environment="production",
            service="pilotcore-finance-engine",
            operation="inspect",
            status="stabilizing",
        )
    )


def _mock_logs(*, ok: bool = True):
    payload = {
        "ok": ok,
        "logs": [] if not ok else [{"timestamp": "2026-05-20T01:00:00Z", "message": "Error: connection refused to database"}],
        "sources_checked": ["deployment_logs"] if ok else [],
        "errors": [] if ok else ["logs unavailable"],
        "all_sources_failed": not ok,
    }
    return patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value=payload,
    )


def test_why_is_mongodb_failed_resolves_from_cached_report():
    _seed_report("mongo-why")
    resolution = resolve_failed_service_target("why is MongoDB failed?", session_id="mongo-why")
    assert resolution.ok is True
    assert resolution.target is not None
    assert resolution.target.row["service"] == "MongoDB"
    assert resolution.target.row["project"] == "pilotcore-sales-engine"


def test_create_fix_plan_for_talking_avatar_worker_resolves_worker():
    _seed_report("worker-plan")
    resolution = resolve_failed_service_target(
        "create fix plan for talking-avatar-worker",
        session_id="worker-plan",
    )
    assert resolution.ok is True
    assert resolution.target is not None
    assert resolution.target.row["service"] == "worker"
    assert resolution.target.row["project"] == "talking-avatar-worker"


def test_active_thread_does_not_hijack_mongodb():
    _seed_report("mongo-hijack")
    _seed_active_thread("mongo-hijack")
    assert is_provider_followup_request("why is MongoDB failed?", session_id="mongo-hijack") is False
    with _mock_logs():
        packed = resolve_handler("why is MongoDB failed?", session_id="mongo-hijack")
    assert packed is not None
    reply, intent, meta = packed
    assert intent == "failed_service_diagnosis"
    assert meta.get("active_thread_override") == "true"
    assert meta.get("service") == "MongoDB"
    assert "pilotcore-finance-engine" not in meta.get("service", "")
    assert "MongoDB" in reply
    assert "pilotcore-sales-engine" in reply


def test_logs_unavailable_still_produces_diagnostic_next_steps():
    _seed_report("logs-gap")
    with _mock_logs(ok=False):
        reply, intent, meta = compose_failed_service_investigation_reply(
            "why is MongoDB failed?",
            session_id="logs-gap",
        )
    assert reply is not None
    assert intent == "failed_service_diagnosis"
    assert meta["service"] == "MongoDB"
    assert "unavailable" in reply.lower()
    assert "Most useful next checks:" in reply


def test_duplicate_service_names_ask_clarification():
    _seed_report("dup-clarify")
    store_provider_wide_health_result(
        session_id="dup-clarify",
        provider="railway",
        payload={
            "services": [
                {"service": "api", "project": "alpha", "environment": "production", "status": "failed", "health": "failed"},
                {"service": "api", "project": "beta", "environment": "production", "status": "failed", "health": "failed"},
            ],
            "counts": {"total": 2, "healthy": 0, "failed": 2, "unknown": 0},
            "failures": [
                {"service": "api", "project": "alpha", "environment": "production", "status": "failed", "health": "failed"},
                {"service": "api", "project": "beta", "environment": "production", "status": "failed", "health": "failed"},
            ],
            "unknown": [],
        },
        summary={"total": 2, "healthy": 0, "failed": 2, "unknown": 0},
    )
    reply, intent, meta = compose_failed_service_investigation_reply("why is api failed?", session_id="dup-clarify")
    assert intent == "failed_service_investigation_clarify"
    assert "alpha" in reply
    assert "beta" in reply
