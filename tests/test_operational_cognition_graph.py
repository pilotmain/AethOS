# SPDX-License-Identifier: Apache-2.0
"""Operational cognition graph tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.route_trace import clear_route_traces_for_tests, save_last_route_trace
from aethos_core.chat.operational_master_router import resolve_operational_master_route
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operational_cognition.cognition_graph import plan_operational_cognition, resolve_operational_cognition
from aethos_core.operational_memory_graph.memory_graph import load_operational_memory_graph
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.operational_result_store import clear_operational_results_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_operational_results_for_tests()
    clear_route_traces_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_operational_results_for_tests()
    clear_route_traces_for_tests()


def _seed_health(session_id: str) -> None:
    rows = [
        {
            "service": "MongoDB",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "failed",
            "service_id": "svc-mongo",
        }
    ]
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": rows, "counts": {"total": 1, "failed": 1}, "failures": rows, "unknown": []},
        summary={"total": 1, "failed": 1},
    )


def _mock_logs():
    return patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": ["unavailable"], "all_sources_failed": True},
    )


def test_plan_operational_cognition_produces_reasoning_chain():
    _seed_health("cog-plan")
    decision = plan_operational_cognition("why is MongoDB failed?", session_id="cog-plan")
    assert decision.intent == "diagnose_failure"
    assert decision.scope in {"provider_service", "failed_service", "provider_wide"}
    assert decision.confidence > 0
    assert decision.reasoning_chain
    assert decision.capabilities
    assert decision.execution_strategy == "failed_service_preemption"


def test_resolve_operational_cognition_e2e_mongodb_failed():
    _seed_health("cog-e2e")
    with _mock_logs():
        decision = resolve_operational_cognition("why is MongoDB failed?", session_id="cog-e2e")
    assert decision is not None
    assert decision.intent == "failed_service_diagnosis"
    assert decision.route_id == "failed_service_preemption"
    assert decision.meta.get("cognition_intent") == "diagnose_failure"
    assert decision.meta.get("reasoning_chain")
    assert "vercel_why_down" in decision.blocked_routes
    assert "operational_cognition" in decision.meta.get("route_trace", "")


def test_master_router_delegates_to_cognition_graph():
    _seed_health("cog-master")
    with _mock_logs():
        decision = resolve_operational_master_route("why is MongoDB failed?", session_id="cog-master")
    assert decision is not None
    assert decision.meta.get("cognition_intent") == "diagnose_failure"
    assert decision.route_id == "failed_service_preemption"


def test_internal_diagnostics_via_cognition_graph():
    save_last_route_trace(
        session_id="cog-internal",
        meta={"route_id": "failed_service_preemption", "route_trace": "failed_service_preemption → failed_service_diagnosis"},
        intent="failed_service_diagnosis",
    )
    decision = resolve_operational_cognition("show route trace", session_id="cog-internal")
    assert decision is not None
    assert decision.route_id == "internal_diagnostics"
    assert decision.meta.get("cognition_intent") == "inspect_route_trace"


def test_operational_memory_graph_loads_unified_context():
    _seed_health("cog-mem")
    graph = load_operational_memory_graph(session_id="cog-mem")
    assert graph.short_term.has_provider_wide_health
    assert graph.infrastructure.get("provider") == "railway"
    assert graph.user_preferences.get("output_format") == "summary" or graph.user_preferences.get("output_format")


def test_resolve_chat_turn_includes_cognition_metadata():
    _seed_health("cog-chat")
    with _mock_logs():
        result = resolve_chat_turn("why is MongoDB failed?", session_id="cog-chat", apply_relational_layer=False)
    assert result.meta.get("cognition_intent") == "diagnose_failure"
    assert result.meta.get("route_id") == "failed_service_preemption"
