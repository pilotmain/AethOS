# SPDX-License-Identifier: Apache-2.0
"""Post-mutation verification routing tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.cognition_exception_boundary import safe_resolve_operational_turn
from aethos_core.operation_lifecycle.lifecycle_resolver import _service_phrase_from_text
from aethos_core.operation_lifecycle.operation_state_store import reset_operation_state_store_for_tests
from aethos_core.operations.mutations.lifecycle_authority import EXECUTION_COMPLETED_STATE
from aethos_core.post_mutation_verification.verification_intent_router import (
    classify_verification_intent_with_context,
    reset_pending_verification_for_tests,
    route_post_mutation_verification,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    reset_operation_state_store_for_tests()
    reset_pending_verification_for_tests()
    yield
    reset_operation_state_store_for_tests()
    reset_pending_verification_for_tests()


def _seed_execution_job(*, session_id: str = "default", service: str = "MongoDB") -> str:
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
            "verification_state": "verification_running",
            "restart_verification_state": "stabilizing",
            "restart_command_submitted": True,
            "provider_result": {"restart_command_submitted": True, "ok": True},
            "railway_before_snapshot": {"latest_deployment_status": "failed"},
            "railway_after_snapshot": {"latest_deployment_status": "failed"},
            "restart_service_health": "failed",
            "canonical_lifecycle_state": EXECUTION_COMPLETED_STATE,
            "lifecycle_summary": "Mutation restart on MongoDB · restart requested · stabilizing",
            "preflight_match_key": f"railway:restart:{service.lower()}",
            "provider_evidence_bundle": {"log_summary": "wiredtiger startup activity"},
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


def test_verify_health_uses_latest_lifecycle() -> None:
    _seed_execution_job()
    reply = route_post_mutation_verification("verify health", session_id="default")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "post_mutation_verify_health"
    assert "MongoDB" in body
    assert "pilotcore-sales-engine / production / MongoDB" in body
    assert meta.get("route_id") == "post_mutation_verification"


def test_did_it_recover_uses_latest_lifecycle() -> None:
    _seed_execution_job()
    reply = route_post_mutation_verification("did it recover?", session_id="default")
    assert reply is not None
    assert "MongoDB" in reply[0]


def test_fetch_logs_after_restart_uses_latest_lifecycle() -> None:
    _seed_execution_job()
    reply = route_post_mutation_verification("fetch logs after restart", session_id="default")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "post_mutation_fetch_logs"
    assert "MongoDB" in body
    assert "Fetching logs after the latest" in body


def test_what_changed_after_restart_uses_comparator() -> None:
    _seed_execution_job()
    reply = route_post_mutation_verification("what changed after restart?", session_id="default")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "post_mutation_what_changed"
    assert "Before restart:" in body
    assert "Change summary:" in body


def test_top_5_logs_checks_startup_marker() -> None:
    _seed_execution_job()
    for job in job_store.list_all():
        if job.job_type == "mutation_execution":
            job.params["provider_evidence_bundle"] = {
                "log_summary": "application startup complete; listening on port 8080",
            }
    reply = route_post_mutation_verification(
        "can you check top 5 logs to see if application started?",
        session_id="default",
    )
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "post_mutation_startup_log_check"
    assert "Startup marker:" in body
    assert "MongoDB" in body


def test_no_generic_system_health_response() -> None:
    _seed_execution_job()
    with patch(
        "aethos_core.chat.handlers.runtime_status_reply",
        return_value="GENERIC SYSTEM HEALTH",
    ):
        result = safe_resolve_operational_turn("verify health", session_id="default")
    assert result is not None
    assert "GENERIC SYSTEM HEALTH" not in result.reply
    assert "MongoDB" in result.reply


def test_classify_verify_health_intent() -> None:
    assert classify_verification_intent_with_context("verify health") == "verify_health"


def test_classify_startup_log_intent() -> None:
    _seed_execution_job()
    intent = classify_verification_intent_with_context(
        "can you check top 5 logs to see if application started?",
        session_id="default",
    )
    assert intent == "startup_log_check"
