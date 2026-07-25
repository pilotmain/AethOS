# SPDX-License-Identifier: Apache-2.0
"""Fallback context resolver tests."""

from __future__ import annotations

import pytest

from aethos_core.chat.route_trace import clear_route_traces_for_tests, save_last_route_trace
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.fallback_context_resolver import resolve_fallback_context
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.world_state_store import clear_world_model_for_tests, save_investigation_state


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    clear_route_traces_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    clear_route_traces_for_tests()


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
        }
    ]


def _seed(session_id: str) -> None:
    rows = _rows()
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": rows, "counts": {"total": 1, "failed": 1}, "failures": rows, "unknown": []},
        summary={"total": 1, "failed": 1},
    )


def test_prompt_mentions_mongodb_resolves_target():
    _seed("wm-fallback-prompt")
    ctx = resolve_fallback_context(
        text="what do we know so far about MongoDB?",
        session_id="wm-fallback-prompt",
    )
    assert ctx is not None
    assert ctx.service == "MongoDB"
    assert ctx.project == "pilotcore-sales-engine"
    assert "MongoDB" in ctx.target


def test_last_route_trace_target_recovered():
    save_last_route_trace(
        session_id="wm-fallback-trace",
        meta={
            "route_id": "failed_service_preemption",
            "matched_target": "pilotcore-sales-engine / production / MongoDB",
            "route_trace": "failed_service_preemption → failed_service_diagnosis",
        },
        intent="failed_service_diagnosis",
    )
    ctx = resolve_fallback_context(text="what should we do next?", session_id="wm-fallback-trace")
    assert ctx is not None
    assert ctx.service == "MongoDB"
    assert ctx.target == "pilotcore-sales-engine / production / MongoDB"


def test_health_report_row_recovered():
    _seed("wm-fallback-health")
    ctx = resolve_fallback_context(text="is restart safe?", session_id="wm-fallback-health")
    assert ctx is not None
    assert ctx.service == "MongoDB"
    assert ctx.source in {"health_report", "explicit_service_mention", "world_model_state"}


def test_recent_diagnosis_target_recovered_from_trace():
    save_last_route_trace(
        session_id="wm-fallback-diag",
        meta={
            "route_id": "world_model_investigation",
            "matched_target": "pilotcore-sales-engine / production / MongoDB",
            "route_trace": "world_model_investigation → recap",
        },
        intent="world_model_investigation_recap",
    )
    ctx = resolve_fallback_context(text="what changed?", session_id="wm-fallback-diag")
    assert ctx is not None
    assert ctx.service == "MongoDB"


def test_world_model_state_enriches_evidence_summary():
    _seed("wm-fallback-state")
    row = _rows()[0]
    save_investigation_state(
        InvestigationState(
            target=target_label_from_row(row),
            session_id="wm-fallback-state",
            service="MongoDB",
            project="pilotcore-sales-engine",
            environment="production",
            evidence=["fresh_wiredtiger_logs", "stale_service_events", "failed_runtime_status"],
            next_best_action="Refresh Railway service events and inspect logs around the latest failure window.",
        )
    )
    ctx = resolve_fallback_context(text="what do we know so far about MongoDB?", session_id="wm-fallback-state")
    assert ctx is not None
    assert "WiredTiger" in ctx.evidence_summary
    assert "stale service events" in ctx.evidence_summary
