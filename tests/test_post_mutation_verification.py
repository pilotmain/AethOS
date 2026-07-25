# SPDX-License-Identifier: Apache-2.0
"""Post-mutation verification routing and reply tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.capabilities.capability_executor import execute_cognition_strategy
from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import reset_operation_state_store_for_tests
from aethos_core.repair_memory.repair_attempt_memory import reset_repair_memory_for_tests
from aethos_core.operations.mutations.lifecycle_authority import EXECUTION_COMPLETED_STATE, VERIFIED_STATE
from aethos_core.operational_cognition.types import OperationalCognitionDecision
from aethos_core.post_mutation_verification.verification_followup_router import (
    compose_post_mutation_verification_reply,
    is_post_mutation_verification_intent,
)
from aethos_core.post_mutation_verification.verification_status_classifier import classify_verification_status
from aethos_core.post_mutation_verification.before_after_comparator import compare_before_after
from aethos_core.post_mutation_verification.verification_evidence_collector import collect_verification_evidence
from aethos_core.post_mutation_verification.verification_context import load_verification_context
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _reset_store():
    reset_operation_state_store_for_tests()
    reset_repair_memory_for_tests()
    reset_global_lifecycle_index_for_tests()
    yield
    reset_operation_state_store_for_tests()
    reset_repair_memory_for_tests()
    reset_global_lifecycle_index_for_tests()


def _seed_execution_job(
    *,
    session_id: str = "default",
    service: str = "MongoDB",
    verification_state: str = "verification_running",
    verified: bool = False,
    restart_verification_state: str = "stabilizing",
    before_status: str = "failed",
    after_status: str = "failed",
    log_summary: str = "",
    restart_command_submitted: bool = True,
) -> str:
    pf = authority.create_job(
        title="Restart MongoDB",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": service,
            "target": {
                "service_name": service,
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
            },
            "preflight_status": "ready_for_mutation_approval",
            "preflight_match_key": f"railway:restart:{service.lower()}",
            "mutation_execution_approved": True,
            "is_current": True,
        },
        session_id=session_id,
        auto_run=False,
    )
    exec_job = authority.create_job(
        title="Restart MongoDB execution",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": service,
            "target": {
                "service_name": service,
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
            },
            "preflight_job_id": pf.id,
            "executed": True,
            "execution_state": "execution_completed",
            "verification_state": verification_state,
            "verified": verified,
            "restart_verification_state": restart_verification_state,
            "restart_command_submitted": restart_command_submitted,
            "restart_service_health": "failed" if after_status == "failed" else "healthy",
            "railway_before_snapshot": {
                "service_id": "svc-mongo",
                "latest_deployment_status": before_status,
            },
            "railway_after_snapshot": {
                "service_id": "svc-mongo",
                "latest_deployment_status": after_status,
            },
            "provider_result": {"restart_command_submitted": restart_command_submitted, "ok": restart_command_submitted},
            "canonical_lifecycle_state": VERIFIED_STATE if verified else EXECUTION_COMPLETED_STATE,
            "lifecycle_summary": f"Mutation restart on {service} · restart requested · stabilizing",
            "preflight_match_key": f"railway:restart:{service.lower()}",
            "provider_evidence_bundle": {"log_summary": log_summary} if log_summary else {},
        },
        session_id=session_id,
        auto_run=False,
    )
    pf_job = job_store.get(pf.id)
    if pf_job:
        pf_job.params["mutation_execution_job_id"] = exec_job.id
    job_store.complete_with_result(
        exec_job.id,
        full_result="done",
        summary="done",
        preview="done",
        provider="mutation_execution",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )
    return exec_job.id


def test_verify_health_after_restart() -> None:
    _seed_execution_job(restart_verification_state="stabilizing", log_summary="wiredtiger startup")
    reply = compose_post_mutation_verification_reply("verify health", session_id="default")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "post_mutation_verify_health"
    assert meta.get("route_id") == "post_mutation_verification"
    assert "verification:" in body.lower()
    assert "MongoDB" in body


def test_did_it_recover_unconfirmed() -> None:
    _seed_execution_job(
        after_status="failed",
        log_summary="wiredtiger storage engine activity only",
        restart_verification_state="restart_unverified",
    )
    reply = compose_post_mutation_verification_reply("did it recover?", session_id="default")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "post_mutation_did_recover"
    assert "Not fully verified yet" in body
    assert "WiredTiger" in body or "failed" in body.lower()


def test_did_it_recover_verified() -> None:
    _seed_execution_job(
        verified=True,
        verification_state="verified",
        after_status="success",
        restart_verification_state="restart_transition_detected",
        log_summary="application startup complete; listening",
    )
    reply = compose_post_mutation_verification_reply("did it recover?", session_id="default")
    assert reply is not None
    body, _intent, _meta = reply
    assert "Yes — recovery appears verified" in body


def test_what_changed_after_restart() -> None:
    _seed_execution_job(
        before_status="failed",
        after_status="failed",
        log_summary="wiredtiger logs, stale service events",
    )
    reply = compose_post_mutation_verification_reply("what changed after restart?", session_id="default")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "post_mutation_what_changed"
    assert "Before restart:" in body
    assert "After restart:" in body
    assert "Change summary:" in body


def test_remains_failed_after_mutation() -> None:
    _seed_execution_job(
        after_status="failed",
        verification_state="verification_failed",
        restart_verification_state="verification_failed",
    )
    ctx = load_verification_context(session_id="default", text="verify health")
    assert ctx is not None
    evidence = collect_verification_evidence(ctx)
    comparison = compare_before_after(evidence)
    status = classify_verification_status(evidence, comparison)
    assert status in {"failed_after_mutation", "regressed", "unconfirmed"}


def test_startup_logs_verify_restart() -> None:
    _seed_execution_job(
        verified=True,
        verification_state="verified",
        after_status="success",
        restart_verification_state="log_restart_detected",
        log_summary="application startup complete; listening on port 8080",
    )
    ctx = load_verification_context(session_id="default", text="verify health")
    assert ctx is not None
    evidence = collect_verification_evidence(ctx)
    comparison = compare_before_after(evidence)
    status = classify_verification_status(evidence, comparison)
    assert status == "verified"


def test_low_signal_logs_keep_status_unconfirmed() -> None:
    _seed_execution_job(
        after_status="failed",
        restart_verification_state="restart_unverified",
        log_summary="wiredtiger recovery log only",
    )
    ctx = load_verification_context(session_id="default", text="verify health")
    assert ctx is not None
    evidence = collect_verification_evidence(ctx)
    comparison = compare_before_after(evidence)
    status = classify_verification_status(evidence, comparison)
    assert status in {"unconfirmed", "failed_after_mutation", "regressed"}


def test_verification_routes_before_world_model() -> None:
    _seed_execution_job()
    decision = OperationalCognitionDecision(
        intent="mutation",
        scope="active_target",
        provider="railway",
        target="MongoDB",
        confidence=0.9,
        reasoning_chain=[],
        execution_strategy="explicit_mutation",
        capabilities=["mutation"],
    )
    with patch(
        "aethos_core.world_model.safe_world_model_runtime.safe_route_world_model_followup",
    ) as world_model:
        result = execute_cognition_strategy(decision, "verify health", session_id="default")
    assert result.handled is True
    assert result.meta.get("route_id") == "post_mutation_verification" or result.route_id in {
        "post_mutation_verification",
        "operation_lifecycle",
    }
    assert "MongoDB" in result.reply
    world_model.assert_not_called()


def test_is_post_mutation_verification_intent() -> None:
    assert is_post_mutation_verification_intent("verify health")
    assert is_post_mutation_verification_intent("what changed after restart?")
    assert not is_post_mutation_verification_intent("why is MongoDB failed")
