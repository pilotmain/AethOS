# SPDX-License-Identifier: Apache-2.0
"""Phase 11.8.1 — Trigger.dev live validation & external runner honesty tests."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.external_execution_truth.execution_store import clear_external_execution_for_tests, get_execution_meta, upsert_execution_meta
from aethos_core.external_execution_truth.orphaned_job_detection import detect_orphaned_jobs, reconcile_orphaned_job
from aethos_core.external_execution_truth.runtime import assess_external_execution_runtime
from aethos_core.external_execution_truth.trigger_dispatch_truth import resolve_runner_mode
from aethos_core.job_truth.honest_replies import compose_honest_progress_inquiry_reply
from aethos_core.job_truth.lifecycle_language import canonical_job_state
from aethos_core.jobs.job_notifications import clear_job_notifications_for_tests
from aethos_core.jobs.job_runtime import create_governed_job, process_trigger_callback
from aethos_core.jobs.job_state import clear_durable_jobs_for_tests, get_job
from aethos_core.live_operational_grounding.regression_guardrails import assess_regression_guardrails
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix


@pytest.fixture(autouse=True)
def _embedded_by_default(monkeypatch):
    monkeypatch.setenv("TRIGGER_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    clear_durable_jobs_for_tests()
    clear_job_notifications_for_tests()
    clear_external_execution_for_tests()


def test_embedded_runner_mode_by_default():
    assert resolve_runner_mode() == "embedded"


def test_external_dispatch_awaits_callback(monkeypatch):
    monkeypatch.setenv("TRIGGER_ENABLED", "true")
    monkeypatch.setenv("TRIGGER_API_KEY", "test-key")
    monkeypatch.setenv("TRIGGER_PROJECT_ID", "proj-test")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    with patch("aethos_core.jobs.trigger_adapter._attempt_trigger_api_dispatch") as mock_dispatch:
        mock_dispatch.return_value = {"ok": True, "external_id": "run-123", "api_reachable": True}
        result = create_governed_job(job_type="research_scan", session_id="test-1181-ext", entity_name="Market Researcher")
        job_id = result["job"]["job_id"]
        job = get_job(job_id)
        assert job is not None
        assert job.get("status") in {"awaiting_callback", "dispatching", "running"}
        meta = get_execution_meta(job_id)
        assert meta is not None
        assert meta.get("runner_mode") == "external"
        assert meta.get("dispatch_status") == "awaiting_callback"

    get_settings.cache_clear()


def test_missing_callback_keeps_bounded_confidence(monkeypatch):
    monkeypatch.setenv("TRIGGER_ENABLED", "true")
    monkeypatch.setenv("TRIGGER_API_KEY", "test-key")
    monkeypatch.setenv("TRIGGER_PROJECT_ID", "proj-test")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    with patch("aethos_core.jobs.trigger_adapter._attempt_trigger_api_dispatch") as mock_dispatch:
        mock_dispatch.return_value = {"ok": True, "external_id": "run-456", "api_reachable": True}
        result = create_governed_job(job_type="gtm_synthesis", session_id="test-1181-miss", entity_name="Product Strategist")
        job_id = result["job"]["job_id"]

    reply = compose_honest_progress_inquiry_reply(session_id="test-1181-miss")
    lower = reply.lower()
    assert "still thinking" not in lower
    assert "callback" in lower or "external" in lower or "completed" in lower or "awaiting" in lower
    get_settings.cache_clear()


def test_webhook_completion_completes_external_job(monkeypatch):
    monkeypatch.setenv("TRIGGER_ENABLED", "true")
    monkeypatch.setenv("TRIGGER_API_KEY", "test-key")
    monkeypatch.setenv("TRIGGER_PROJECT_ID", "proj-test")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    with patch("aethos_core.jobs.trigger_adapter._attempt_trigger_api_dispatch") as mock_dispatch:
        mock_dispatch.return_value = {"ok": True, "external_id": "run-789", "api_reachable": True}
        result = create_governed_job(job_type="research_scan", session_id="test-1181-hook", entity_name="Market Researcher")
        job_id = result["job"]["job_id"]

    callback = process_trigger_callback(
        {"job_id": job_id, "status": "completed", "output": {"summary": "External research pass complete."}},
    )
    assert callback.get("ok") is True
    job = get_job(job_id)
    assert job is not None
    assert job.get("status") == "completed"
    meta = get_execution_meta(job_id)
    assert meta is not None
    assert meta.get("last_callback_at") is not None
    get_settings.cache_clear()


def test_degraded_fallback_runs_embedded(monkeypatch):
    monkeypatch.setenv("TRIGGER_ENABLED", "true")
    monkeypatch.setenv("TRIGGER_API_KEY", "test-key")
    monkeypatch.setenv("TRIGGER_PROJECT_ID", "proj-test")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    with patch("aethos_core.jobs.trigger_adapter._attempt_trigger_api_dispatch") as mock_dispatch:
        mock_dispatch.return_value = {"ok": False, "reason": "api_unreachable", "api_reachable": False}
        result = create_governed_job(job_type="research_scan", session_id="test-1181-deg", entity_name="Market Researcher")
        job_id = result["job"]["job_id"]
        time.sleep(1.2)
        job = get_job(job_id)
        assert job is not None
        meta = get_execution_meta(job_id)
        assert meta is not None
        assert meta.get("runner_mode") == "degraded"
        assert job.get("status") == "completed"

    get_settings.cache_clear()


def test_orphaned_job_detection(monkeypatch):
    monkeypatch.setenv("TRIGGER_ENABLED", "true")
    monkeypatch.setenv("TRIGGER_API_KEY", "test-key")
    monkeypatch.setenv("TRIGGER_PROJECT_ID", "proj-test")
    monkeypatch.setenv("TRIGGER_ORPHANED_JOB_MINUTES", "1")
    from aethos_core.config import get_settings
    from aethos_core.jobs.job_state import create_job_record, update_job

    get_settings.cache_clear()
    job = create_job_record(job_type="research_scan", session_id="test-1181-orphan", entity_name="Market Researcher")
    job_id = job["job_id"]
    update_job(job_id, status="awaiting_callback")
    upsert_execution_meta(
        job_id,
        session_id="test-1181-orphan",
        runner_mode="external",
        dispatch_status="awaiting_callback",
        dispatched_at=time.time() - 7200,
    )

    orphaned = detect_orphaned_jobs(session_id="test-1181-orphan")
    assert len(orphaned) >= 1
    reconcile = reconcile_orphaned_job(job_id)
    assert reconcile.get("orphaned") is True
    assert canonical_job_state(get_job(job_id) or {}) == "orphaned"
    get_settings.cache_clear()


def test_external_execution_runtime_assessment():
    assessment = assess_external_execution_runtime(session_id="test-1181-assess", channel="telegram")
    assert assessment["phase"] == "11.8.2"
    assert "runner_mode" in assessment


def test_aggregate_runtime_phase_1181():
    agg = assess_conversational_operational_grounding(session_id="test-1181-agg", channel="telegram")
    assert agg["phase"] == "11.8.2"
    assert "external_execution_truth_runtime" in agg


def test_capability_matrix_includes_external_execution():
    rows = build_capability_truth_matrix()
    assert any(r["id"] == "external_execution_truth_runtime" for r in rows)


def test_regression_guardrails_block_fake_active_execution():
    guard = assess_regression_guardrails(reply="The agents are working on the analysis right now.")
    assert guard["guardrails_qualified"] is False
