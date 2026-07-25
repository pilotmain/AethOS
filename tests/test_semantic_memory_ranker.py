# SPDX-License-Identifier: Apache-2.0
"""Semantic memory ranker tests."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.continuity_intelligence.operational_focus_model import clear_focus_for_tests, update_operational_focus
from aethos_core.continuity_intelligence.semantic_memory_ranker import best_memory_candidate, rank_memory_candidates
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


def _seed_job(session_id: str, service: str) -> None:
    preflight = authority.create_job(
        title=f"Railway restart {service}",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": service,
            "target": {"project_name": "demo", "environment": "production", "service_name": service},
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="Mutation execution",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": service,
            "execution_state": "execution_stabilizing",
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_execution_job(job=job_store.get(execution.id))


def test_speakglobal_recall_beats_pilotos_topology():
    _seed_job("rank-session", "speakglobal-ai")
    _seed_job("rank-session", "pilotos-api")
    update_operational_focus(session_id="rank-session", provider="railway", service="pilotos-api", operation="restart")
    best = best_memory_candidate(
        session_id="rank-session",
        user_text="what were we doing with speakglobal-ai?",
        service_phrase="speakglobal-ai",
    )
    assert best is not None
    assert best.service == "speakglobal-ai"


def test_recent_operational_focus_increases_ranking():
    update_operational_focus(session_id="focus-session", provider="railway", service="pilotos-api", operation="restart")
    ranked = rank_memory_candidates(
        session_id="focus-session",
        user_text="can you check again?",
        service_phrase="",
    )
    assert ranked
    assert ranked[0].service == "pilotos-api"


def test_stale_unrelated_topology_loses_when_service_named():
    _seed_job("stale-rank", "pilotos-api")
    best = best_memory_candidate(
        session_id="stale-rank",
        user_text="what were we doing with speakglobal-ai?",
        service_phrase="speakglobal-ai",
    )
    assert best is None or best.service != "pilotos-api"
