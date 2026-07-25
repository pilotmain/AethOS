# SPDX-License-Identifier: Apache-2.0
"""Repair outcome memory tests."""

from __future__ import annotations

import pytest

from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import reset_operation_state_store_for_tests
from aethos_core.post_mutation_verification.verification_reply_composer import build_verification_bundle
from aethos_core.repair_memory.historical_repair_lookup import lookup_latest_for_target
from aethos_core.repair_memory.repair_attempt_memory import reset_repair_memory_for_tests
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
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
    verified: bool = False,
    before_status: str = "failed",
    after_status: str = "failed",
    log_summary: str = "wiredtiger storage engine activity only",
    restart_verification_state: str = "restart_unverified",
    verification_state: str = "verification_running",
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
            "restart_command_submitted": True,
            "restart_service_health": "failed" if after_status == "failed" else "healthy",
            "railway_before_snapshot": {"latest_deployment_status": before_status},
            "railway_after_snapshot": {"latest_deployment_status": after_status},
            "provider_result": {"restart_command_submitted": True, "ok": True},
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


def test_regressed_verification_records_failed_repair_outcome() -> None:
    exec_id = _seed_execution_job(
        after_status="failed",
        before_status="failed",
        restart_verification_state="verification_failed",
        verification_state="verification_failed",
    )
    bundle = build_verification_bundle(session_id="default", text="verify health")
    assert bundle is not None
    ctx, _evidence, _comparison, status = bundle
    assert status in {"regressed", "failed_after_mutation"}

    latest = lookup_latest_for_target(ctx.target_path)
    assert latest is not None
    assert latest.helped is False
    assert latest.result in {"regressed", "failed_after_mutation"}
    assert latest.health_after == "failed"
    assert "Restart did not resolve" in latest.lesson or "did not resolve" in latest.lesson.lower()

    exec_job = job_store.get(exec_id)
    assert exec_job is not None
    assert exec_job.params.get("repair_learning")
    assert exec_job.params["repair_learning"]["helped"] is False


def test_failed_after_mutation_records_failed_repair_outcome() -> None:
    _seed_execution_job(
        after_status="failed",
        restart_verification_state="restart_unverified",
        verification_state="verification_running",
        log_summary="wiredtiger recovery log only",
    )
    bundle = build_verification_bundle(session_id="default", text="verify health")
    assert bundle is not None
    ctx, _evidence, _comparison, status = bundle
    assert status in {"failed_after_mutation", "regressed", "unconfirmed"}

    latest = lookup_latest_for_target(ctx.target_path)
    assert latest is not None
    assert latest.helped is False
    assert latest.operation == "restart"


def test_verified_records_successful_repair_outcome() -> None:
    _seed_execution_job(
        verified=True,
        verification_state="verified",
        after_status="success",
        restart_verification_state="restart_transition_detected",
        log_summary="application startup complete; listening",
    )
    bundle = build_verification_bundle(session_id="default", text="verify health")
    assert bundle is not None
    ctx, _evidence, _comparison, status = bundle
    assert status == "verified"

    latest = lookup_latest_for_target(ctx.target_path)
    assert latest is not None
    assert latest.helped is True
    assert "helped" in latest.lesson.lower()
