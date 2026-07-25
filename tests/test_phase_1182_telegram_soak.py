# SPDX-License-Identifier: Apache-2.0
"""Phase 11.8.2 — Telegram soak testing & operational realism validation tests."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from aethos_core.conversation.legacy_polish_api import assess_conversational_operational_grounding
from aethos_core.external_execution_truth.execution_store import clear_external_execution_for_tests, upsert_execution_meta
from aethos_core.external_execution_truth.webhook_security import sign_webhook_payload, validate_webhook_delivery
from aethos_core.jobs.job_notifications import clear_job_notifications_for_tests
from aethos_core.jobs.job_runtime import create_governed_job, process_trigger_callback
from aethos_core.jobs.job_state import clear_durable_jobs_for_tests, get_job
from aethos_core.live_operational_grounding.regression_guardrails import assess_regression_guardrails
from aethos_core.operational_entity_runtime.lightweight_agent_registry import clear_operational_entities_for_tests
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.telegram_soak.realism_scoring import score_turn
from aethos_core.telegram_soak.session_truth_ledger import clear_ledger_for_tests, summarize_ledger
from aethos_core.telegram_soak.soak_runner import run_all_compressed, run_soak_scenario
from aethos_core.telegram_soak.soak_scenarios import list_soak_scenarios
from aethos_core.telegram_soak.runtime import assess_telegram_soak_runtime
from aethos_core.telegram_soak.transcript_capture import capture_turn


@pytest.fixture(autouse=True)
def _embedded_by_default(monkeypatch):
    monkeypatch.setenv("TRIGGER_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    clear_operational_entities_for_tests()
    clear_durable_jobs_for_tests()
    clear_job_notifications_for_tests()
    clear_external_execution_for_tests()
    clear_ledger_for_tests()


def test_canonical_soak_scenarios_present():
    scenarios = list_soak_scenarios()
    ids = {s["id"] for s in scenarios}
    assert "delayed_railway_recovery" in ids
    assert "parallel_investigation_drift" in ids
    assert "stale_callback_missing_webhook" in ids
    assert "retry_storm" in ids
    assert len(scenarios) == 5


def test_realism_scoring_penalizes_overconfidence():
    bad = score_turn(
        reply="Everything is healthy now. The analysis completed successfully.",
        scenario_id="stale_callback_missing_webhook",
    )
    assert bad["hallucination_risk"] == "high"
    assert bad["operational_realism_score"] < 0.5

    good = score_turn(
        reply=(
            "The latest strategist synthesis job was dispatched successfully, though the external execution runtime "
            "has not produced a fresh completion callback within the expected verification window yet."
        ),
        scenario_id="stale_callback_missing_webhook",
    )
    assert good["hallucination_risk"] == "low"
    assert good["operational_realism_score"] >= 0.5


def test_realism_scoring_parallel_drift_subject_affinity():
    unsafe = score_turn(
        reply="The deployment stabilized successfully on Railway.",
        scenario_id="parallel_investigation_drift",
        user_text="Did the replay stabilize?",
    )
    assert unsafe["ambiguity_handling"] == "unsafe"

    safe = score_turn(
        reply=(
            "I believe you're referring to the earlier replay continuity investigation rather than the Railway restart, "
            "though operational confidence is currently moderate because multiple active threads exist."
        ),
        scenario_id="parallel_investigation_drift",
        user_text="Did the replay stabilize?",
    )
    assert safe["ambiguity_handling"] == "safe"


def test_truth_ledger_capture_and_summary():
    capture_turn(
        session_id="test-1182-ledger",
        scenario_id="retry_storm",
        user_text="Any updates?",
        reply="Several operational verification cycles encountered transient execution delays and are being retried automatically.",
    )
    summary = summarize_ledger(session_id="test-1182-ledger")
    assert summary["entry_count"] == 1
    assert summary["average_realism"] > 0


def test_webhook_signature_idempotency_and_sequence(monkeypatch):
    monkeypatch.setenv("TRIGGER_WEBHOOK_SECRET", "test-secret-1182")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    result = create_governed_job(job_type="research_scan", session_id="test-1182-webhook", entity_name="Market Researcher")
    job_id = result["job"]["job_id"]
    upsert_execution_meta(job_id, runner_mode="external", dispatch_status="awaiting_callback", dispatched_at=time.time())

    payload = {"job_id": job_id, "status": "completed", "output": {}, "delivery_id": "del-1", "sequence": 1}
    payload["signature"] = sign_webhook_payload(payload)
    first = process_trigger_callback(payload)
    assert first.get("ok") is True
    assert first.get("duplicate") is not True

    second = process_trigger_callback(payload)
    assert second.get("duplicate") is True

    stale_payload = {"job_id": job_id, "status": "completed", "output": {}, "delivery_id": "del-2", "sequence": 1}
    stale_payload["signature"] = sign_webhook_payload(stale_payload)
    stale = process_trigger_callback(stale_payload)
    assert stale.get("ok") is False
    assert stale.get("reason") == "stale_callback_sequence"

    get_settings.cache_clear()


def test_webhook_rejects_invalid_signature(monkeypatch):
    monkeypatch.setenv("TRIGGER_WEBHOOK_SECRET", "test-secret-1182")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    result = create_governed_job(job_type="gtm_synthesis", session_id="test-1182-bad-sig", entity_name="Product Strategist")
    job_id = result["job"]["job_id"]
    payload = {"job_id": job_id, "status": "completed", "output": {}}
    check = validate_webhook_delivery(job_id=job_id, payload=payload, signature="bad-signature")
    assert check.get("ok") is False
    assert check.get("reason") == "invalid_signature"
    get_settings.cache_clear()


def test_compressed_soak_delayed_railway_recovery():
    result = run_soak_scenario(
        scenario_id="delayed_railway_recovery",
        session_id="test-1182-railway",
        mode="compressed",
    )
    assert result.get("ok") is True
    assert result.get("turn_count") == 3
    replies = " ".join(str(t.get("entry", {}).get("reply_preview") or "") for t in result.get("turns") or [])
    assert assess_regression_guardrails(reply=replies)["guardrails_qualified"] is True


def test_compressed_soak_stale_callback_scenario():
    result = run_soak_scenario(
        scenario_id="stale_callback_missing_webhook",
        session_id="test-1182-callback",
        mode="compressed",
    )
    assert result.get("ok") is True
    last_turn = (result.get("turns") or [])[-1]
    reply = str(last_turn.get("entry", {}).get("reply_preview") or "").lower()
    assert "awaiting" in reply or "callback" in reply or "running" in reply or "activity" in reply
    assert last_turn["scores"]["hallucination_risk"] != "high"


def test_run_all_compressed_soak():
    with patch.dict("os.environ", {"TRIGGER_ENABLED": "false"}, clear=False):
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        bundle = run_all_compressed(session_prefix="test-1182-all")
        assert bundle.get("ok") is True
        assert bundle.get("scenario_count") == 5
        get_settings.cache_clear()


def test_telegram_soak_runtime_assessment():
    assessment = assess_telegram_soak_runtime(session_id="test-1182-runtime", channel="telegram")
    assert assessment["phase"] == "11.8.2"
    assert "ledger" in assessment
    assert len(assessment.get("scenarios") or []) == 5


def test_aggregate_runtime_phase_1182():
    agg = assess_conversational_operational_grounding(session_id="test-1182-agg", channel="telegram")
    assert agg["phase"] == "11.8.2"
    assert "telegram_soak_runtime" in agg
    assert "external_execution_truth_runtime" in agg


def test_capability_matrix_includes_telegram_soak():
    rows = build_capability_truth_matrix()
    assert any(r["id"] == "telegram_soak_runtime" for r in rows)
    assert any(r["id"] == "external_execution_truth_runtime" for r in rows)


def test_regression_guardrails_block_retry_spam():
    scored = score_turn(reply="Retrying... Retrying... Retrying...", scenario_id="retry_storm")
    assert scored["notification_quality"] == "noisy"
    assert scored["retry_behavior"] == "fatiguing"


def test_stale_callback_job_not_marked_completed_without_webhook():
    from aethos_core.jobs.job_state import create_job_record, update_job

    job = create_job_record(
        job_type="gtm_synthesis",
        session_id="test-1182-orphan-job",
        entity_name="Product Strategist",
    )
    job_id = job["job_id"]
    upsert_execution_meta(
        job_id,
        session_id="test-1182-orphan-job",
        runner_mode="external",
        dispatch_status="awaiting_callback",
        dispatched_at=time.time() - 1200,
    )
    update_job(job_id, status="awaiting_callback")
    record = get_job(job_id)
    assert record is not None
    assert record.get("status") == "awaiting_callback"
