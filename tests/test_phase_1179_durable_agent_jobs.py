# SPDX-License-Identifier: Apache-2.0
"""Phase 11.7.9 — Durable agent jobs tests."""

from __future__ import annotations

import time

import pytest

from aethos_core.agent_progression_memory.progression_store import clear_progression_for_tests
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.jobs.job_governance import assess_job_governance
from aethos_core.jobs.job_runtime import create_governed_job, enqueue_agent_workspace_jobs
from aethos_core.jobs.job_scheduler import schedule_recovery_windows
from aethos_core.jobs.job_state import clear_durable_jobs_for_tests, list_jobs
from aethos_core.jobs.runtime import assess_durable_agent_jobs_runtime
from aethos_core.operational_entity_runtime.lightweight_agent_registry import clear_operational_entities_for_tests
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix


@pytest.fixture(autouse=True)
def _embedded_runner(monkeypatch):
    monkeypatch.setenv("TRIGGER_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    clear_operational_entities_for_tests()
    clear_progression_for_tests()
    clear_durable_jobs_for_tests()
    from aethos_core.jobs.job_notifications import clear_job_notifications_for_tests

    clear_job_notifications_for_tests()


def test_job_governance_blocks_unknown():
    gov = assess_job_governance(job_type="unknown_type")
    assert gov["allowed"] is False


def test_create_research_scan_job():
    result = create_governed_job(job_type="research_scan", session_id="test-1179", entity_name="Market Researcher")
    assert result["ok"] is True
    assert result["job"]["job_type"] == "research_scan"


def test_agent_creation_registers_background_jobs():
    from aethos_core.agents.runtime.subagent_session_store import clear_subagent_sessions_for_tests, list_subagent_sessions

    clear_subagent_sessions_for_tests()
    session = "test-1179-create"
    result = resolve_chat_turn(
        "create two agents, one development one qa, assign them skills",
        session_id=session,
        channel="telegram",
    )
    assert "initialized" in result.reply.lower()
    assert "background jobs registered" not in result.reply.lower()
    assert "gtm" not in result.reply.lower()
    sessions = list_subagent_sessions(parent_session_id=session)
    assert len(sessions) >= 2


def test_progress_inquiry_after_job_completion():
    session = "test-1179-update"
    resolve_chat_turn(
        "create two agents, one development one qa",
        session_id=session,
        channel="telegram",
    )
    follow = resolve_chat_turn("Any update on the agents?", session_id=session, channel="telegram")
    assert "don't have visibility" not in follow.reply.lower()
    assert "development" in follow.reply.lower() or "qa" in follow.reply.lower() or "active" in follow.reply.lower()


def test_job_status_query():
    from aethos_core.conversation.progression_compat import compose_job_status_reply

    session = "test-1179-status"
    enqueue_agent_workspace_jobs(session_id=session, agent_names=["Research agent", "Analysis agent"])
    time.sleep(1.0)
    reply = compose_job_status_reply(session_id=session)
    assert "job" in reply.lower() or "queued" in reply.lower() or "running" in reply.lower()
    jobs = list_jobs(session_id=session)
    assert len(jobs) >= 1


def test_recovery_window_scheduling():
    jobs = schedule_recovery_windows(session_id="test-1179-recovery", subject="Railway deployment recovery")
    assert len(jobs) == 4
    assert all(j.get("job_type") == "recovery_window_check" for j in jobs)


def test_durable_jobs_runtime_assessment():
    session = "test-1179-assess"
    create_governed_job(job_type="research_scan", session_id=session, entity_name="Market Researcher")
    assessment = assess_durable_agent_jobs_runtime(session_id=session, channel="telegram")
    assert assessment["phase"] == "11.7.9"


def test_aggregate_runtime_phase_1179():
    agg = assess_conversational_operational_grounding(session_id="test-1179-agg", channel="telegram")
    assert agg["phase"] == "11.8.2"
    assert "durable_agent_jobs_runtime" in agg
    assert "job_truth_runtime" in agg


def test_capability_matrix_includes_durable_jobs():
    rows = build_capability_truth_matrix()
    assert any(r["id"] == "durable_agent_jobs_runtime" for r in rows)
