# SPDX-License-Identifier: Apache-2.0
"""Continuity timeline tests."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.continuity_intelligence.continuity_timeline import build_continuity_timeline, timeline_for_service
from aethos_core.continuity_intelligence.operational_focus_model import clear_focus_for_tests, get_operational_focus
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_threads_for_tests()
    clear_focus_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    clear_focus_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def test_restart_approval_execution_followup_chronology():
    preflight = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={"provider": "railway", "operation_type": "restart", "target_name": "speakglobal-ai"},
        source="test",
        session_id="timeline-session",
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="Mutation execution",
        job_type="mutation_execution",
        params={"provider": "railway", "operation_type": "restart", "target_name": "speakglobal-ai", "execution_state": "execution_stabilizing"},
        source="test",
        session_id="timeline-session",
        auto_run=False,
    )
    sync_thread_from_execution_job(job=job_store.get(execution.id))
    entries = build_continuity_timeline(session_id="timeline-session")
    assert len(entries) >= 2
    services = {entry.service for entry in entries}
    assert "speakglobal-ai" in services


def test_operational_focus_persisted():
    preflight = authority.create_job(
        title="Railway restart",
        job_type="mutation_preflight",
        params={"provider": "railway", "operation_type": "restart", "target_name": "pilotos-api"},
        source="test",
        session_id="focus-timeline",
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    focus = get_operational_focus(session_id="focus-timeline")
    assert focus.get("service") == "pilotos-api"


def test_expired_thread_still_reconstructable_from_timeline():
    execution = authority.create_job(
        title="Mutation execution",
        job_type="mutation_execution",
        params={"provider": "railway", "operation_type": "restart", "target_name": "speakglobal-ai"},
        source="test",
        session_id="expired-timeline",
        auto_run=False,
    )
    sync_thread_from_execution_job(job=job_store.get(execution.id))
    clear_threads_for_tests()
    entries = timeline_for_service(session_id="expired-timeline", service_phrase="speakglobal-ai")
    assert entries
