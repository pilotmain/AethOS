# SPDX-License-Identifier: Apache-2.0
"""Pending action continuation tests."""

from __future__ import annotations

import pytest

from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, save_binding
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store
from aethos_core.task_frame.confirmation_continuation import compose_pending_action_continuation_reply
from aethos_core.task_frame.pending_action import clear_pending_actions_for_tests, get_pending_action, offer_retry_preflight_action


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    clear_topology_for_tests()
    clear_pending_actions_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    clear_topology_for_tests()
    clear_pending_actions_for_tests()
    job_store.clear_for_tests()


def _seed_thread(session_id: str = "pending-action") -> None:
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            service_id="svc-speakglobal",
            github_repo="pilotmain/speakglobal-ai",
            source_verified=True,
        )
    )
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
                "service_id": "svc-speakglobal",
                "resolved": True,
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)


def test_please_do_after_correction_creates_restart_preflight():
    _seed_thread()
    offer_retry_preflight_action(
        session_id="pending-action",
        provider="railway",
        project="adequate-luck",
        environment="production",
        service="speakglobal-ai",
        operation="restart",
        source_binding="pilotmain/speakglobal-ai",
    )
    reply = compose_pending_action_continuation_reply("please do", session_id="pending-action")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "pending_action_preflight_created"
    assert "speakglobal-ai" in body
    assert "pilotmain/speakglobal-ai" in body
    assert "job-" in body
    assert get_pending_action(session_id="pending-action") is None


def test_go_ahead_continues_offered_retry():
    _seed_thread(session_id="pending-go")
    offer_retry_preflight_action(
        session_id="pending-go",
        provider="railway",
        project="adequate-luck",
        environment="production",
        service="speakglobal-ai",
        operation="restart",
        source_binding="pilotmain/speakglobal-ai",
    )
    reply = compose_pending_action_continuation_reply("go ahead", session_id="pending-go")
    assert reply is not None
    assert reply[1] == "pending_action_preflight_created"


def test_stale_pending_action_expires():
    from aethos_core.task_frame.pending_action import PendingAction, store_pending_action
    from datetime import UTC, datetime, timedelta

    action = PendingAction(
        session_id="pending-stale",
        provider="railway",
        project="adequate-luck",
        environment="production",
        service="speakglobal-ai",
        expires_at=(datetime.now(UTC) - timedelta(hours=1)).isoformat(),
    )
    store_pending_action(action)
    reply = compose_pending_action_continuation_reply("please do", session_id="pending-stale")
    assert reply is None


def test_wrong_confirmation_does_not_trigger_mutation():
    _seed_thread(session_id="pending-wrong")
    offer_retry_preflight_action(
        session_id="pending-wrong",
        provider="railway",
        project="adequate-luck",
        environment="production",
        service="speakglobal-ai",
        operation="restart",
    )
    reply = compose_pending_action_continuation_reply("maybe later", session_id="pending-wrong")
    assert reply is None
    assert get_pending_action(session_id="pending-wrong") is not None
