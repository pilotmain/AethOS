# SPDX-License-Identifier: Apache-2.0
"""Provider memory bridge tests."""

from __future__ import annotations

import pytest

from aethos_core.continuity_intelligence.operational_focus_model import clear_focus_for_tests, get_operational_focus
from aethos_core.operational_skill_runtime.evidence_collector import UniversalEvidenceBundle
from aethos_core.operational_skill_runtime.provider_memory_bridge import persist_operation_memory, recall_operation_memory
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, get_active_thread
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    clear_focus_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    clear_focus_for_tests()
    job_store.clear_for_tests()


def test_persist_operation_memory_updates_focus_and_thread():
    job = authority.create_job(
        title="Mutation execution",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "target": {"project_name": "pilotos", "environment": "production", "service_name": "pilotos-api"},
            "mutation_execution_approved_at_iso": "2026-05-25T01:50:41Z",
            "restart_command_submitted": True,
            "command": "serviceInstanceRedeploy",
        },
        source="test",
        session_id="memory-bridge",
        auto_run=False,
    )
    thread = OperationalThreadState(
        session_id="memory-bridge",
        provider="railway",
        project="pilotos",
        environment="production",
        service="pilotos-api",
        operation="restart",
        execution_job_id=job.id,
        status="stabilizing",
    )
    from aethos_core.operational_thread_memory.thread_persistence import save_thread_state

    save_thread_state(thread)

    universal = UniversalEvidenceBundle(
        provider="railway",
        operation="restart",
        target={"service_name": "pilotos-api", "project_name": "pilotos", "environment": "production"},
        command_submitted=True,
        command_name="serviceInstanceRedeploy",
        approved_at="2026-05-25T01:50:41Z",
        latest_log_timestamp="2026-05-25T01:51:03Z",
        startup_log_observed_after_approval=True,
        verification_status="restart_evidence_detected",
    )
    result = persist_operation_memory(session_id="memory-bridge", job=job, universal=universal)
    assert result["ok"] is True
    focus = get_operational_focus(session_id="memory-bridge")
    assert focus.get("provider") == "railway"
    assert focus.get("service") == "pilotos-api"
    assert focus.get("command_name") == "serviceInstanceRedeploy"
    recalled = recall_operation_memory(session_id="memory-bridge")
    assert recalled["ok"] is True
    active = get_active_thread(session_id="memory-bridge")
    assert active is not None
    assert active.last_evidence.get("startup_log_observed_after_approval") is True
