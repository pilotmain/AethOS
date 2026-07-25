# SPDX-License-Identifier: Apache-2.0
"""Internal diagnostics routing tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.route_trace import (
    clear_route_traces_for_tests,
    compose_internal_route_trace_reply,
    is_internal_diagnostics_query,
    save_last_route_trace,
)
from aethos_core.chat.operation_preflight_prompts import create_operation_preflight_job_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operations.intents import infer_operation_preflight_intent


@pytest.fixture(autouse=True)
def _clean():
    clear_route_traces_for_tests()
    yield
    clear_route_traces_for_tests()


def test_check_api_meta_for_route_trace_routes_internal():
    save_last_route_trace(
        session_id="internal-1",
        meta={
            "route_id": "failed_service_preemption",
            "matched_module": "failed_service_investigation.global_preemption",
            "matched_target": "pilotcore-sales-engine / production / MongoDB",
            "blocked_routes": "vercel_why_down,generic_fix_plan",
            "route_trace": "failed_service_preemption → failed_service_diagnosis",
        },
        intent="failed_service_diagnosis",
    )
    result = resolve_chat_turn(
        "Check API meta or logs for route_trace",
        session_id="internal-1",
        apply_relational_layer=False,
    )
    assert result.intent == "internal_route_trace_diagnostics"
    assert result.meta.get("route_id") == "internal_diagnostics"
    assert "failed_service_preemption" in result.reply
    assert "MongoDB" in result.reply
    assert create_operation_preflight_job_reply(
        "Check API meta or logs for route_trace",
        session_id="internal-1",
    ) is None


def test_show_route_trace_routes_internal():
    save_last_route_trace(
        session_id="internal-2",
        meta={"route_id": "failed_service_preemption", "route_trace": "failed_service_preemption → failed_service_diagnosis"},
        intent="failed_service_diagnosis",
    )
    result = resolve_chat_turn("show route trace", session_id="internal-2", apply_relational_layer=False)
    assert result.intent == "internal_route_trace_diagnostics"
    assert "route_id" in result.reply


def test_which_route_won_routes_internal():
    result = resolve_chat_turn("which route won?", session_id="internal-3", apply_relational_layer=False)
    assert result.intent == "internal_route_trace_diagnostics"
    assert "don't have route_trace metadata" in result.reply.lower()


def test_check_vercel_logs_still_routes_vercel():
    assert is_internal_diagnostics_query("check Vercel logs") is False
    preflight = infer_operation_preflight_intent("check Vercel logs", session_id="internal-vercel")
    assert preflight is not None
    _title, _job_type, params = preflight
    assert params.get("provider") == "vercel"


def test_no_vercel_preflight_for_route_trace_query():
    assert infer_operation_preflight_intent("Check API meta or logs for route_trace", session_id="internal-block") is None


def test_is_internal_diagnostics_query_recognizes_dev_phrases():
    assert is_internal_diagnostics_query("check response meta for route_id")
    assert is_internal_diagnostics_query("show blocked_routes from last turn")
    assert not is_internal_diagnostics_query("show MongoDB error logs")
