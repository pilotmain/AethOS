# SPDX-License-Identifier: Apache-2.0
"""Actionable operational follow-up tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.actionable_followup import (
    classify_followup_action,
    compose_actionable_followup_reply,
    execute_followup_action,
    FollowupAction,
)
from aethos_core.operational_thread_memory.completion_watch import clear_completion_watches_for_tests, get_completion_watch
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_threads_for_tests()
    clear_completion_watches_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    clear_completion_watches_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _seed_thread(session_id: str = "actionable-followup") -> None:
    preflight = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "target": {
                "project_name": "adequate-luck",
                "environment": "production",
                "service_name": "speakglobal-ai",
                "resolved": True,
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "target": {
                "project_name": "adequate-luck",
                "environment": "production",
                "service_name": "speakglobal-ai",
            },
            "mutation_execution_approved_at_iso": "2026-05-20T10:00:00+00:00",
            "execution_state": "execution_stabilizing",
            "restart_verification_state": "restart_requested",
            "provider_evidence_bundle": {
                "approved_at": "2026-05-20T10:00:00+00:00",
                "logs_excerpt": [
                    {
                        "timestamp": "2026-05-20T10:01:30+00:00",
                        "level": "INFO",
                        "message": "Application startup complete.",
                    }
                ],
                "verification": {"status": "restart_requested"},
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    sync_thread_from_execution_job(job=stored)


def test_update_me_once_restart_done_creates_completion_watch():
    _seed_thread("watch-test")
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread

    thread = get_active_thread(session_id="watch-test")
    assert thread is not None
    action = classify_followup_action("update me once restart is done and its status?", thread)
    assert action is not None
    assert action.action_type == "create_completion_watch"
    result = execute_followup_action(action, thread, session_id="watch-test")
    assert result.watch_created is True
    assert get_completion_watch(session_id="watch-test") is not None
    assert "I'll watch the active" in result.body
    assert "Railway" in result.body
    assert "job-" in result.body


def test_can_you_check_checks_active_thread_evidence():
    _seed_thread("check-test")
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread

    thread = get_active_thread(session_id="check-test")
    action = classify_followup_action("can you check?", thread)
    assert action is not None
    assert action.action_type == "check_status"
    result = execute_followup_action(action, thread, session_id="check-test")
    assert "Latest log timestamp" in result.body
    assert "Conclusion" in result.body
    assert "Tell me what you need" not in result.body


def test_tell_me_last_timestamp_returns_latest_log_timestamp():
    _seed_thread("timestamp-test")
    reply = compose_actionable_followup_reply("tell me the last timestamp after restart?", session_id="timestamp-test")
    assert reply is not None
    body, intent, meta = reply
    assert intent.startswith("actionable_") or intent.startswith("provider_followup_")
    assert "2026-05-20T10:01:30+00:00" in body
    assert "Application startup complete." in body
    assert meta.get("execution_job_id")


def test_no_generic_fallback_when_active_thread_exists():
    from aethos_core.api.main import app

    _seed_thread("no-generic")
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "can you read logs and see if the restart happened?", "session_id": "no-generic"},
    )
    body = response.json()
    assert body.get("intent", "").startswith("actionable_") or body.get("intent", "").startswith("provider_followup_")
    assert "I'm ready to help" not in body["reply"]
    assert "Tell me what you need" not in body["reply"]
    assert "Conclusion" in body["reply"]


def test_stale_logs_do_not_verify_restart():
    _seed_thread("stale-logs")
    job = job_store.list_all()[-1]
    job.params["provider_evidence_bundle"] = {
        "approved_at": "2026-05-20T10:00:00+00:00",
        "logs_excerpt": [
            {"timestamp": "2026-05-20T09:59:00+00:00", "level": "INFO", "message": "Old boot line"},
        ],
    }
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread

    thread = get_active_thread(session_id="stale-logs")
    result = execute_followup_action(
        FollowupAction("check_logs", user_text="check logs"),
        thread,
        session_id="stale-logs",
    )
    assert "Restart verified" not in result.body
    assert result.conclusion in {"inconclusive", "still_stabilizing", "restart_unverified", "restart_evidence_detected"}
