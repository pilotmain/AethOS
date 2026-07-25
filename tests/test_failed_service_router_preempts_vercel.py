# SPDX-License-Identifier: Apache-2.0
"""Failed-service router preempts Vercel/generic diagnostics."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.handlers import resolve_handler
from aethos_core.chat.operation_preflight_prompts import create_operation_preflight_job_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.failed_service_investigation.failed_service_router import compose_failed_service_investigation_reply
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, save_thread_state
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.operations.intents import infer_operation_preflight_intent
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
            "counts": {"total": 3, "healthy": 0, "failed": 3, "unknown": 0},
            "failures": rows,
            "unknown": [],
        },
        summary={"total": 3, "healthy": 0, "failed": 3, "unknown": 0},
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


def test_why_is_mongodb_failed_does_not_create_vercel_preflight():
    _seed_report("preempt-vercel")
    assert infer_operation_preflight_intent("why is MongoDB failed?", session_id="preempt-vercel") is None
    assert create_operation_preflight_job_reply("why is MongoDB failed?", session_id="preempt-vercel") is None


def test_why_is_mongodb_failed_resolves_railway_mongodb_row():
    _seed_report("preempt-mongo")
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": ["unavailable"], "all_sources_failed": True},
    ):
        reply, intent, meta = compose_failed_service_investigation_reply(
            "why is MongoDB failed?",
            session_id="preempt-mongo",
        )
    assert intent == "failed_service_diagnosis"
    assert meta["service"] == "MongoDB"
    assert meta["project"] == "pilotcore-sales-engine"
    assert "MongoDB" in reply
    assert "pilotcore-sales-engine" in reply


def test_fix_plan_for_project_name_resolves_worker_row():
    _seed_report("preempt-worker")
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": [], "all_sources_failed": True},
    ):
        reply, intent, meta = compose_failed_service_investigation_reply(
            "create fix plan for talking-avatar-worker",
            session_id="preempt-worker",
        )
    assert intent == "failed_service_fix_plan"
    assert meta["service"] == "worker"
    assert meta["project"] == "talking-avatar-worker"
    assert "talking-avatar-worker" in reply


def test_active_thread_does_not_hijack_named_failed_row():
    _seed_report("preempt-hijack")
    _seed_active_thread("preempt-hijack")
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": [], "all_sources_failed": True},
    ):
        packed = resolve_handler("why is MongoDB failed?", session_id="preempt-hijack")
    assert packed is not None
    reply, intent, meta = packed
    assert intent == "failed_service_diagnosis"
    assert meta["service"] == "MongoDB"
    assert "pilotcore-finance-engine" not in meta["service"]


def test_generic_llm_path_not_used_for_named_failed_service():
    _seed_report("preempt-llm")
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": [], "all_sources_failed": True},
    ):
        result = resolve_chat_turn(
            "create fix plan for talking-avatar-worker",
            session_id="preempt-llm",
            apply_relational_layer=False,
        )
    assert result.intent == "failed_service_fix_plan"
    assert result.used_llm is False
