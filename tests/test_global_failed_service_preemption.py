# SPDX-License-Identifier: Apache-2.0
"""Global failed-service preemption tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.handlers import resolve_handler
from aethos_core.chat.operation_preflight_prompts import create_operation_preflight_job_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.failed_service_investigation.global_preemption import (
    detect_failed_service_reference,
    route_failed_service_intent,
    should_preempt_to_failed_service,
)
from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    yield
    clear_provider_wide_health_for_tests()


def _rows() -> list[dict]:
    return [
        {"service": "MongoDB", "project": "pilotcore-sales-engine", "environment": "production", "status": "failed", "health": "failed", "deployment_state": "failed", "service_id": "svc-mongo"},
        {"service": "worker", "project": "talking-avatar-worker", "environment": "production", "status": "failed", "health": "failed", "deployment_state": "crashed", "service_id": "svc-worker"},
    ]


def _seed(session_id: str) -> None:
    rows = _rows()
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": rows, "counts": {"total": 2, "failed": 2}, "failures": rows, "unknown": []},
        summary={"total": 2, "failed": 2},
    )


def _mock_logs():
    return patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": ["unavailable"], "all_sources_failed": True},
    )


def test_why_is_mongodb_failed_preempts_vercel():
    _seed("gp-vercel")
    assert should_preempt_to_failed_service("why is MongoDB failed?", session_id="gp-vercel")
    assert infer_operation_preflight_intent("why is MongoDB failed?", session_id="gp-vercel") is None
    assert create_operation_preflight_job_reply("why is MongoDB failed?", session_id="gp-vercel") is None


def test_fix_plan_for_project_preempts_generic():
    _seed("gp-fix")
    with _mock_logs():
        result = resolve_chat_turn("create fix plan for talking-avatar-worker", session_id="gp-fix", apply_relational_layer=False)
    assert result.intent == "failed_service_fix_plan"
    assert result.used_llm is False
    assert "talking-avatar-worker" in result.reply


def test_inspect_events_preempts_generic_guidance():
    _seed("gp-events")
    with _mock_logs(), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": True, "events": [{"created_at": "2026-01-01T00:00:00Z", "state": "FAILED", "message": "Deployment dep-1 state=FAILED"}]},
    ):
        result = resolve_chat_turn("inspect MongoDB service events", session_id="gp-events", apply_relational_layer=False)
    assert result.intent == "failed_service_events"
    assert "pilotcore-sales-engine" in result.reply
    assert "Events:" in result.reply


def test_show_mongodb_error_logs_still_works():
    _seed("gp-logs")
    with _mock_logs():
        reply, intent, meta = route_failed_service_intent("show MongoDB error logs", session_id="gp-logs")
    assert intent == "failed_service_logs"
    assert meta["service"] == "MongoDB"


def test_unknown_service_still_owned_by_cognition_not_vercel():
    _seed("gp-unknown")
    assert detect_failed_service_reference("why is redis failed?", session_id="gp-unknown") is None
    assert should_preempt_to_failed_service("why is redis failed?", session_id="gp-unknown") is True
    reply, intent, _meta = route_failed_service_intent("why is redis failed?", session_id="gp-unknown")
    assert reply is not None
    assert intent == "failed_service_investigation_not_found"


def test_resolve_handler_uses_global_preemption():
    _seed("gp-handler")
    with _mock_logs():
        packed = resolve_handler("why is MongoDB failed?", session_id="gp-handler")
    assert packed is not None
    reply, intent, meta = packed
    assert intent == "failed_service_diagnosis"
    assert meta["service"] == "MongoDB"
