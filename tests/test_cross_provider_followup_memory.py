# SPDX-License-Identifier: Apache-2.0
"""Cross-provider follow-up memory tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.continuity_intelligence.operational_focus_model import clear_focus_for_tests, get_operational_focus
from aethos_core.conversation.provider_memory.provider_followup_runtime import handle_provider_followup
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
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


def _seed(session_id: str):
    preflight = authority.create_job(
        title="preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "target": {"project_name": "pilotos", "environment": "production", "service_name": "pilotos-api"},
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="execution",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "mutation_execution_approved_at_iso": "2026-05-25T01:50:41Z",
            "provider_evidence_bundle": {
                "approved_at": "2026-05-25T01:50:41Z",
                "command": "serviceInstanceRedeploy",
                "command_submitted": True,
                "logs_excerpt": [
                    {"timestamp": "2026-05-25T01:13:58Z", "message": "old cached line"},
                ],
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    stored.status = stored.status.__class__("completed")
    sync_thread_from_execution_job(job=stored)


def test_followup_updates_operational_focus():
    _seed("cross-followup")
    with patch(
        "aethos_core.providers.railway.railway_log_evidence.fetch_fresh_logs_for_verification",
        return_value={
            "ok": True,
            "logs": [
                {
                    "timestamp": "2026-05-25T01:51:03Z",
                    "level": "INFO",
                    "message": "Application startup complete.",
                    "source": "runtime_cli_logs",
                }
            ],
            "sources_checked": ["runtime_logs_after"],
            "errors": [],
        },
    ):
        result = handle_provider_followup(session_id="cross-followup", user_text="did the restart happen?")
    assert result is not None
    focus = get_operational_focus(session_id="cross-followup")
    assert focus.get("provider") == "railway"
    assert focus.get("service") == "pilotos-api"
    assert focus.get("latest_log_timestamp") == "2026-05-25T01:51:03Z"
