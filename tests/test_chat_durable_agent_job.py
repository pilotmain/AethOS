# SPDX-License-Identifier: Apache-2.0
"""Durable multi-agent chat turns — coordination runs as a server-side job.

Long agent work must not be tied to the browser connection: navigating away
must not interrupt it. The chat request enqueues an ``agent_coordination`` job
and returns a ``job_id`` immediately; the run lives on the durable executor.
"""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store, message_for_job_event


@pytest.fixture(autouse=True)
def _isolate_jobs():
    job_executor.drain_queue_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()
    yield
    job_executor.drain_queue_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def test_multi_agent_turn_dispatches_durable_job(monkeypatch):
    monkeypatch.setenv("DURABLE_AGENT_JOBS_ENABLED", "true")
    get_settings.cache_clear()

    from aethos_core.chat.service import resolve_chat_turn

    out = resolve_chat_turn(
        "analyze why the latest Railway deployment failed", session_id="dur-a"
    )

    # The request returns immediately with a tracked job pointer, not the full
    # synchronous coordination output.
    assert out.intent == "agent_coordination_job_created"
    assert out.used_llm is False
    job_id = out.meta.get("proposed_job_id")
    assert isinstance(job_id, str) and job_id.startswith("job-")

    job = job_store.get(job_id)
    assert job is not None
    assert job.job_type == "agent_coordination"
    # The executor thread is not started in unit tests, so the durable job is
    # parked on the queue rather than executed inside the request.
    assert job.status.value in {"queued", "running"}


def test_multi_agent_dispatch_carries_job_meta(monkeypatch):
    monkeypatch.setenv("DURABLE_AGENT_JOBS_ENABLED", "true")
    get_settings.cache_clear()

    from aethos_core.chat.agent_intelligence import multi_agent_job_reply

    handled = multi_agent_job_reply(
        "analyze architecture risks in AethOS", session_id="dur-b"
    )
    assert handled is not None
    body, intent, meta = handled
    assert intent == "agent_coordination_job_created"
    assert meta["proposed_job_type"] == "agent_coordination"
    assert meta["multi_agent_route_selected"] == "true"
    # The reply must tell the operator the work is durable / connection-independent.
    assert "background" in body.lower()
    assert meta["proposed_job_id"] in body


def test_completed_agent_coordination_surfaces_full_plan():
    job = job_store.create(
        title="coordination",
        job_type="agent_coordination",
        session_id="dur-c",
        auto_run=False,
    )
    job_store.begin_running(job.id)
    job_store.complete_with_result(
        job.id,
        full_result="# Consolidated Plan\n\nStep 1 do X.\nStep 2 do Y.",
        summary="Multi-agent coordination — completed",
        preview="Consolidated Plan",
        provider="agent_coordination",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )
    completed = job_store.get(job.id)
    assert completed is not None

    # The completion bubble carries the full consolidated plan into chat (it used
    # to render inline before the run was made durable), not a one-line pointer.
    msg = message_for_job_event(completed, "job_completed")
    assert "Consolidated Plan" in msg
    assert "Step 1 do X." in msg
    assert "Step 2 do Y." in msg


def test_durable_flag_off_keeps_synchronous_path(monkeypatch):
    monkeypatch.setenv("DURABLE_AGENT_JOBS_ENABLED", "false")
    get_settings.cache_clear()
    assert get_settings().durable_agent_jobs_enabled is False
