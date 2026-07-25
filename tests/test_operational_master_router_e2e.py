# SPDX-License-Identifier: Apache-2.0
"""End-to-end operational master router tests via live chat entry points."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.channels.base.channel_adapter import ChannelMessage
from aethos_core.channels.inbound import handle_channel_message
from aethos_core.chat.operation_preflight_prompts import create_operation_preflight_job_reply
from aethos_core.chat.operational_master_router import resolve_operational_master_route
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.operational_result_store import clear_operational_results_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_operational_results_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_operational_results_for_tests()


def _rows() -> list[dict]:
    return [
        {
            "service": "MongoDB",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "failed",
            "service_id": "svc-mongo",
        },
        {
            "service": "worker",
            "project": "talking-avatar-worker",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "crashed",
            "service_id": "svc-worker",
        },
    ]


def _seed_health(session_id: str) -> None:
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


def test_e2e_why_is_mongodb_failed_via_resolve_chat_turn():
    _seed_health("e2e-web")
    with _mock_logs():
        result = resolve_chat_turn("why is MongoDB failed?", session_id="e2e-web", apply_relational_layer=False)
    assert result.intent == "failed_service_diagnosis"
    assert result.meta.get("route_id") == "failed_service_preemption"
    assert "vercel_why_down" in str(result.meta.get("blocked_routes") or "")
    assert create_operation_preflight_job_reply("why is MongoDB failed?", session_id="e2e-web") is None


def test_e2e_fix_plan_via_telegram_entry_point(monkeypatch):
    monkeypatch.setenv("CHANNEL_GATEWAY_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    _seed_health("tg-999-1")
    with _mock_logs():
        turn = handle_channel_message(
            ChannelMessage(
                channel="telegram",
                session_id="tg-999-1",
                external_chat_id="999",
                external_user_id="1",
                text="create fix plan for talking-avatar-worker",
            )
        )
    assert turn.intent == "failed_service_fix_plan"
    assert turn.meta.get("route_id") == "failed_service_preemption"
    assert "talking-avatar-worker" in turn.reply


def test_e2e_inspect_events_via_resolve_chat_turn():
    _seed_health("e2e-events")
    with _mock_logs(), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": True, "events": [{"created_at": "2026-01-01T00:00:00Z", "state": "FAILED", "message": "Deployment dep-1 state=FAILED"}]},
    ):
        result = resolve_chat_turn("inspect MongoDB service events", session_id="e2e-events", apply_relational_layer=False)
    assert result.intent == "failed_service_events"
    assert result.meta.get("route_id") == "failed_service_preemption"


def test_e2e_unknown_service_blocks_vercel_preflight():
    _seed_health("e2e-redis")
    preflight = create_operation_preflight_job_reply("why is redis failed?", session_id="e2e-redis")
    assert preflight is None
    decision = resolve_operational_master_route("why is redis failed?", session_id="e2e-redis")
    assert decision is not None
    assert decision.route_id == "failed_service_preemption"


def test_e2e_health_report_fallback_across_session_prefix():
    _seed_health("tg-chat-42-user-7")
    with _mock_logs():
        result = resolve_chat_turn("why is MongoDB failed?", session_id="tg-chat-42-user-9", apply_relational_layer=False)
    assert result.intent == "failed_service_diagnosis"
    assert result.meta.get("route_id") == "failed_service_preemption"
