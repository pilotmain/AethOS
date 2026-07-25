# SPDX-License-Identifier: Apache-2.0
"""Context reconstructor tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.aethos_identity.context_reconstructor import (
    extract_operational_resource_phrase,
    maybe_reconstruct_active_thread,
    search_provider_targets,
)
from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, get_active_thread
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_threads_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def test_pilotos_api_resolves_railway_service():
    result = search_provider_targets("pilotos-api")
    assert result.resolved is not None
    assert result.resolved.service_name == "pilotos-api"
    assert result.resolved.project_name == "pilotos"


def test_speakglobal_ai_resolves_railway_service():
    result = search_provider_targets("speakglobal-ai")
    assert result.resolved is not None
    assert result.resolved.service_name == "speakglobal-ai"


def test_unknown_service_has_no_resolved_target():
    result = search_provider_targets("this-service-does-not-exist-xyz")
    assert result.resolved is None


def test_top_5_logs_extracts_service_phrase():
    phrase = extract_operational_resource_phrase("can you check top 5 logs and its timestamp for pilotos-api?")
    assert phrase == "pilotos-api"


def test_did_restart_happen_reconstructs_recent_job_thread():
    preflight = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "target": {"project_name": "pilotos", "environment": "production", "service_name": "pilotos-api"},
        },
        source="test",
        session_id="job-reconstruct",
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "execution_state": "execution_stabilizing",
            "restart_verification_state": "restart_requested",
        },
        source="test",
        session_id="job-reconstruct",
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    assert stored is not None
    sync_thread_from_execution_job(job=stored)
    clear_threads_for_tests()

    ctx = maybe_reconstruct_active_thread(session_id="job-reconstruct", user_text="did the restart happen?")
    assert ctx is not None
    assert ctx.thread is not None
    assert get_active_thread(session_id="job-reconstruct") is not None
    assert ctx.thread.service == "pilotos-api"


def test_topology_reconstruction_without_job():
    ctx = maybe_reconstruct_active_thread(
        session_id="topology-only",
        user_text="check logs for pilotos-api",
    )
    assert ctx is not None
    assert ctx.source == "provider_topology"
    thread = get_active_thread(session_id="topology-only")
    assert thread is not None
    assert thread.service == "pilotos-api"
