# SPDX-License-Identifier: Apache-2.0
"""Operational query planner scope and routing tests."""

from __future__ import annotations

import pytest

from aethos_core.conversation.provider_memory.conversational_memory_router import is_provider_followup_request
from aethos_core.conversation.provider_memory.followup_intent_classifier import classify_followup_intent
from aethos_core.conversation.provider_memory.provider_followup_runtime import handle_provider_followup
from aethos_core.operational_planner.query_planner import plan_operational_query
from aethos_core.operational_planner.scope_classifier import classify_operational_scope
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, save_thread_state
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    job_store.clear_for_tests()


def _seed_active_railway_thread(session_id: str = "planner-scope"):
    save_thread_state(
        OperationalThreadState(
            session_id=session_id,
            provider="railway",
            project="pilotos",
            environment="production",
            service="pilotos-api",
            operation="restart",
            status="stabilizing",
        )
    )
    preflight = authority.create_job(
        title="preflight",
        job_type="mutation_preflight",
        params={"provider": "railway", "operation_type": "restart", "target_name": "pilotos-api"},
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="execution",
        job_type="mutation_execution",
        params={"provider": "railway", "operation_type": "restart", "target_name": "pilotos-api"},
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_execution_job(job=execution)


def test_all_services_in_railway_is_provider_wide():
    text = (
        "check all the services available in railway and report back with "
        "running - healthy and failed with the service names"
    )
    plan = plan_operational_query(text, session_id="scope-wide")
    assert plan.scope == "provider_wide"
    assert plan.provider == "railway"
    assert plan.intent == "inventory_health_report"
    assert plan.overrides_active_thread is True


def test_check_service_health_with_active_thread_is_active_target():
    _seed_active_railway_thread("scope-active")
    plan = plan_operational_query("check service health", session_id="scope-active")
    assert plan.scope == "active_target"
    assert plan.intent == "health_check"
    assert plan.overrides_active_thread is False


def test_restart_pilotos_api_is_mutation_scope():
    plan = plan_operational_query("restart pilotos-api", session_id="scope-mutation")
    assert plan.scope == "provider_service"
    assert plan.intent == "mutation"
    assert plan.action_type == "mutation"


def test_all_failed_services_is_provider_wide():
    plan = plan_operational_query("show all failed services in railway", session_id="scope-failed")
    assert classify_operational_scope("show all failed services in railway") == "provider_wide"
    assert plan.scope == "provider_wide"


def test_active_thread_does_not_override_provider_wide_request():
    _seed_active_railway_thread("scope-override")
    text = "check all services in railway and report healthy vs failed"
    assert is_provider_followup_request(text, session_id="scope-override") is False
    thread = OperationalThreadState(
        session_id="scope-override",
        provider="railway",
        service="pilotos-api",
        operation="restart",
    )
    assert classify_followup_intent(text, thread) is None


def test_report_back_alone_does_not_hijack_provider_wide_when_all_services_present():
    _seed_active_railway_thread("scope-report-back")
    text = "check all the services available in railway and report back with running - healthy and failed"
    result = handle_provider_followup(session_id="scope-report-back", user_text=text)
    assert result is None
