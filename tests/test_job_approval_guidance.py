# SPDX-License-Identifier: Apache-2.0
"""Tests for job approval guidance."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.jobs.job_approval_guidance import (
    APPROVAL_ACTION_MUTATION,
    compose_job_approval_guidance_reply,
    get_job_approval_guidance,
    is_job_approval_intent,
    mutation_approval_surface,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _mutation_enabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    job_store.clear_for_tests()


def _seed_mutation_preflight(job_id: str = "job-test-approval") -> None:
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "atlas-trader api",
            "user_request": "Restart Railway atlas-trader api service",
        },
        source="test",
        session_id="test-approval",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    stored.params["preflight_status"] = "ready_for_mutation_approval"
    stored.params["mutation_preflight"] = {
        "provider": "railway",
        "operation_type": "restart",
        "target_name": "atlas-trader api",
        "preflight_status": "ready_for_mutation_approval",
        "risk_tier": "T2_service_restart",
    }
    stored.params["risk_tier"] = "T2_service_restart"
    stored.params["blast_radius"] = {"scope": "single_service", "summary": "One Railway service restart"}
    stored.params["rollback_plan"] = {"strategy": "redeploy_previous", "summary": "Redeploy prior deployment"}
    stored.params["is_current"] = True
    stored.params.update(
        {
            "approval_required": True,
            "approval_surface": mutation_approval_surface(),
            "approval_action_label": APPROVAL_ACTION_MUTATION,
            "approval_state": "pending_approval",
            "target_resolved": True,
        }
    )


def test_pending_mutation_preflight_returns_approval_surface():
    _seed_mutation_preflight()
    job = job_store.list_all()[0]
    guidance = get_job_approval_guidance(job.id)
    assert guidance.found is True
    assert guidance.approval_required is True
    assert guidance.approval_state == "pending_approval"
    assert guidance.approval_surface == mutation_approval_surface()
    assert guidance.approval_action_label == APPROVAL_ACTION_MUTATION
    assert guidance.ui_action_available is True
    assert "blast_radius" in (guidance.review_items or [])


def test_non_mutation_tracked_job_says_approval_not_required():
    job = authority.create_job(
        title="Manual note",
        job_type="manual_note",
        params={},
        source="test",
        auto_run=False,
    )
    guidance = get_job_approval_guidance(job.id)
    assert guidance.found is True
    assert guidance.approval_required is False


def test_unknown_job_returns_not_found():
    guidance = get_job_approval_guidance("job-deadbeef")
    assert guidance.found is False
    assert guidance.reason == "job_not_found"


def test_executed_mutation_preflight_reports_execution_state():
    _seed_mutation_preflight()
    job = job_store.list_all()[0]
    job.params["mutation_execution_approved"] = True
    job.params["mutation_execution_job_id"] = "job-exec-123"
    reply = compose_job_approval_guidance_reply(f"where do i approve {job.id}?")
    assert reply is not None
    assert "already passed approval" in reply.lower()


def test_missing_ui_when_mutation_execution_disabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "false")
    get_settings.cache_clear()
    _seed_mutation_preflight()
    job = job_store.list_all()[0]
    guidance = get_job_approval_guidance(job.id)
    assert guidance.ui_action_available is False
    assert guidance.wiring_gap is not None


def test_compose_reply_for_unknown_job_is_aethos_specific():
    reply = compose_job_approval_guidance_reply("where do i approve job-deadbeef?")
    assert reply is not None
    assert "couldn't find" in reply.lower()
    assert mutation_approval_surface() in reply
    assert "Operation Preflights" not in reply
    assert "pr approval" not in reply.lower()
    assert "deployment gate" not in reply.lower()


def test_is_job_approval_intent_detection():
    assert is_job_approval_intent("where do i approve job-abc123?") is True
    assert is_job_approval_intent("status of job-abc123") is False
