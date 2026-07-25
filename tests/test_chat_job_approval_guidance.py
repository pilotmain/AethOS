# SPDX-License-Identifier: Apache-2.0
"""Tests for chat job approval guidance routing."""

from __future__ import annotations

import pytest

from aethos_core.chat.handlers import resolve_handler
from aethos_core.config import get_settings
from aethos_core.jobs.job_approval_guidance import APPROVAL_ACTION_MUTATION, mutation_approval_surface
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import JobStatus, job_store


@pytest.fixture(autouse=True)
def _mutation_enabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    job_store.clear_for_tests()


def _pending_preflight() -> str:
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={"provider": "railway", "operation_type": "restart", "target_name": "atlas-trader api"},
        source="test",
        session_id="test-chat-approval",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = JobStatus.COMPLETED
    stored.params["preflight_status"] = "ready_for_mutation_approval"
    stored.params["target_resolved"] = True
    stored.params["mutation_preflight"] = {
        "provider": "railway",
        "operation_type": "restart",
        "target_name": "atlas-trader api",
        "target_resolved": True,
        "preflight_status": "ready_for_mutation_approval",
    }
    stored.params["is_current"] = True
    return job.id


def test_where_do_i_approve_routes_to_guidance():
    job_id = _pending_preflight()
    packed = resolve_handler(f"where do i approve {job_id}?", session_id="test-chat-approval")
    assert packed is not None
    reply, intent, _meta = packed
    assert intent == "job_approval_guidance"
    assert "Approvals" in reply
    assert "Approve Governed Mutation" in reply
    assert "no restart has been performed yet" in reply.lower() or "no mutation has been performed yet" in reply.lower()
    assert "pr approval" not in reply.lower()
    assert "deployment gate" not in reply.lower()


def test_how_do_i_approve_restart_job():
    job_id = _pending_preflight()
    packed = resolve_handler(f"how do i approve {job_id}?", session_id="test-chat-approval")
    assert packed is not None
    reply, intent, _meta = packed
    assert intent == "job_approval_guidance"
    assert "Approvals" in reply


def test_approve_job_id_intent():
    job_id = _pending_preflight()
    packed = resolve_handler(f"approve {job_id}", session_id="test-chat-approval")
    assert packed is not None
    assert packed[1] == "job_approval_guidance"


def test_where_is_the_approval():
    job_id = _pending_preflight()
    packed = resolve_handler(f"where is the approval for {job_id}?", session_id="test-chat-approval")
    assert packed is not None
    assert packed[1] == "job_approval_guidance"
