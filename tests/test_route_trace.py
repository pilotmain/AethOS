# SPDX-License-Identifier: Apache-2.0
"""Route trace metadata tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

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


def _seed(session_id: str) -> None:
    row = {
        "service": "MongoDB",
        "project": "pilotcore-sales-engine",
        "environment": "production",
        "status": "failed",
        "health": "failed",
        "deployment_state": "failed",
        "service_id": "svc-mongo",
    }
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": [row], "counts": {"total": 1, "failed": 1}, "failures": [row], "unknown": []},
        summary={"total": 1, "failed": 1},
    )


def test_route_trace_present_on_failed_service_route():
    _seed("trace-1")
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": [], "all_sources_failed": True},
    ):
        decision = resolve_operational_master_route("why is MongoDB failed?", session_id="trace-1")
    assert decision is not None
    assert decision.route_id == "failed_service_preemption"
    assert decision.matched_module == "failed_service_investigation.global_preemption"
    assert "vercel_why_down" in decision.blocked_routes
    assert decision.matched_target == "pilotcore-sales-engine / production / MongoDB"
    assert "failed_service_preemption" in decision.trace_chain


def test_route_trace_exposed_in_chat_meta():
    _seed("trace-2")
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": [], "all_sources_failed": True},
    ):
        result = resolve_chat_turn("why is MongoDB failed?", session_id="trace-2", apply_relational_layer=False)
    from aethos_core.chat.route_trace import get_last_route_trace

    assert result.reply.strip()
    trace = get_last_route_trace(session_id="trace-2")
    assert trace is not None
    assert trace.get("route_id") or trace.get("intent")
