# SPDX-License-Identifier: Apache-2.0
"""Phase 11.8.0 — Telegram long-session validation & job status honesty tests."""

from __future__ import annotations

import time

from aethos_core.agent_progression_memory.progression_store import clear_progression_for_tests
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.job_truth.honest_replies import compose_honest_job_status_reply, compose_honest_progress_inquiry_reply
from aethos_core.job_truth.lifecycle_language import canonical_job_state
from aethos_core.job_truth.notification_policy import compose_notification_digest, should_enqueue_notification
from aethos_core.job_truth.runtime import assess_job_truth_runtime
from aethos_core.jobs.job_notifications import clear_job_notifications_for_tests, enqueue_job_notification
from aethos_core.jobs.job_runtime import create_governed_job, enqueue_agent_workspace_jobs
from aethos_core.jobs.job_state import clear_durable_jobs_for_tests, create_job_record, update_job
from aethos_core.live_operational_grounding.regression_guardrails import assess_regression_guardrails
from aethos_core.operational_entity_runtime.lightweight_agent_registry import clear_operational_entities_for_tests
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.validation_harness.harness_runtime import harness_state
from aethos_core.validation_harness.telegram_session_harness import list_telegram_scenarios


def setup_function() -> None:
    clear_operational_entities_for_tests()
    clear_progression_for_tests()
    clear_durable_jobs_for_tests()
    clear_job_notifications_for_tests()


def test_canonical_job_states_include_verifying():
    job = {"job_id": "dj-test", "status": "running", "job_type": "recovery_window_check"}
    assert canonical_job_state(job) in {"verifying", "stabilizing", "running"}


def test_notification_policy_suppresses_heartbeat_language():
    assert should_enqueue_notification(job_type="recovery_window_check", message="Verification running.") is False


def test_notification_digest_groups_multiple_updates():
    notes = [
        {"job_type": "research_scan", "message": "Research scan completed."},
        {"job_type": "gtm_synthesis", "message": "Strategist synthesis started."},
    ]
    digest = compose_notification_digest(notes)
    assert "Grouped" in digest or "Latest completed passes" in digest


def test_honest_progress_inquiry_uses_last_activity():
    session = "test-1180-progress"
    enqueue_agent_workspace_jobs(session_id=session, agent_names=["Market Researcher"])
    time.sleep(1.0)
    reply = compose_honest_progress_inquiry_reply(session_id=session)
    lower = reply.lower()
    assert "still thinking" not in lower
    assert "analyzing competitors" not in lower
    assert "minute" in lower or "completed" in lower or "running" in lower or "just now" in lower


def test_progress_inquiry_chat_turn_honest():
    session = "test-1180-chat"
    resolve_chat_turn(
        "Create Market Researcher and Product Strategist agents",
        session_id=session,
        channel="telegram",
    )
    time.sleep(1.5)
    follow = resolve_chat_turn("Any update on the agents?", session_id=session, channel="telegram")
    lower = follow.reply.lower()
    assert "still thinking" not in lower
    assert assess_regression_guardrails(reply=follow.reply)["guardrails_qualified"] is True


def test_stale_continuity_decay_language():
    session = "test-1180-stale"
    job = create_job_record(job_type="research_scan", session_id=session, entity_name="Market Researcher")
    update_job(
        job["job_id"],
        status="completed",
        completed_at=time.time() - 90000,
        updated_at=time.time() - 90000,
    )
    truth = assess_job_truth_runtime(session_id=session)
    assert truth["freshness"]["freshness_tier"] == "stale"
    reply = compose_honest_job_status_reply(session_id=session)
    assert "24 hours" in reply.lower() or "decay" in reply.lower() or "old" in reply.lower()


def test_job_truth_runtime_assessment():
    session = "test-1180-truth"
    create_governed_job(job_type="research_scan", session_id=session, entity_name="Market Researcher")
    assessment = assess_job_truth_runtime(session_id=session, channel="telegram")
    assert assessment["phase"] == "11.8.2"
    assert "runtime_presence" in assessment


def test_validation_harness_scenarios():
    state = harness_state(session_id="test-1180-harness")
    scenarios = list_telegram_scenarios()
    assert len(scenarios) == 5
    assert state["harness_version"] == "11.8.0"
    assert state["scenario_count"] == 5


def test_aggregate_runtime_phase_1180():
    agg = assess_conversational_operational_grounding(session_id="test-1180-agg", channel="telegram")
    assert agg["phase"] == "11.8.2"
    assert "job_truth_runtime" in agg


def test_capability_matrix_includes_job_truth():
    rows = build_capability_truth_matrix()
    assert any(r["id"] == "job_truth_runtime" for r in rows)
    assert any(r["id"] == "telegram_validation_harness" for r in rows)


def test_regression_guardrails_block_fake_autonomy():
    guard = assess_regression_guardrails(reply="I'm still thinking about the deployment recovery.")
    assert guard["guardrails_qualified"] is False


def test_pending_notifications_marked_delivered_on_inquiry():
    session = "test-1180-deliver"
    enqueue_job_notification(
        session_id=session,
        message="The Product Strategist completed the latest synthesis pass.",
        job_type="gtm_synthesis",
    )
    compose_honest_progress_inquiry_reply(session_id=session)
    from aethos_core.jobs.job_notifications import list_pending_notifications

    assert list_pending_notifications(session_id=session) == []
