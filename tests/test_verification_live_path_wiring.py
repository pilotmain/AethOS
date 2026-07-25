# SPDX-License-Identifier: Apache-2.0
"""Live chat-path wiring tests for post-mutation verification preemption."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import (
    reset_operation_state_store_for_tests,
    upsert_operation_state_from_job,
)
from aethos_core.operations.mutations.lifecycle_authority import EXECUTION_COMPLETED_STATE
from aethos_core.post_mutation_verification.verification_intent_router import reset_pending_verification_for_tests
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    reset_operation_state_store_for_tests()
    reset_global_lifecycle_index_for_tests()
    reset_pending_verification_for_tests()
    yield
    reset_operation_state_store_for_tests()
    reset_global_lifecycle_index_for_tests()
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
    upsert_operation_state_from_job(job_store.get(exec_job.id))
    return exec_job.id


def test_live_verify_health_routes_post_mutation_verification() -> None:
    _seed_execution_job(session_id="default")
    with patch(
        "aethos_core.chat.handlers.runtime_status_reply",
        return_value="GENERIC SYSTEM HEALTH",
    ):
        result = resolve_chat_turn("verify health", session_id="tg-live-1-2", apply_relational_layer=False)
    assert result.intent == "post_mutation_verify_health"
    assert "MongoDB" in result.reply
    assert result.meta.get("route_id") == "post_mutation_verification"
    assert "GENERIC SYSTEM HEALTH" not in result.reply


def test_live_top_5_logs_routes_post_mutation_verification() -> None:
    _seed_execution_job(session_id="default")
    prompt = "can you check top 5 logs to see if application started?"
    with patch(
        "aethos_core.chat.handlers.capability_matrix_reply",
        return_value="CAPABILITY INTRO",
    ):
        result = resolve_chat_turn(prompt, session_id="tg-live-1-2", apply_relational_layer=False)
    assert result.intent == "post_mutation_startup_log_check"
    assert "MongoDB" in result.reply
    assert result.meta.get("route_id") == "post_mutation_verification"
    assert "CAPABILITY INTRO" not in result.reply


def test_live_no_world_model_hijack_for_what_changed() -> None:
    _seed_execution_job(session_id="default")
    with patch(
        "aethos_core.world_model.safe_world_model_runtime._compose_followup_reply",
        return_value=("WORLD MODEL UPDATE", "world_model_what_changed"),
    ):
        result = resolve_chat_turn("what changed after restart?", session_id="tg-live-1-2", apply_relational_layer=False)
    assert "WORLD MODEL UPDATE" not in result.reply
    assert "MongoDB" in result.reply
    assert result.meta.get("route_id") == "post_mutation_verification"


def test_live_explicit_path_continues_pending_verification() -> None:
    _seed_execution_job(session_id="default")
    from aethos_core.post_mutation_verification.verification_intent_router import (
        store_pending_verification_request,
    )

    store_pending_verification_request(
        session_id="tg-live-1-2",
        intent="startup_log_check",
        original_text="can you check top 5 logs to see if application started?",
    )
    result = resolve_chat_turn(
        "pilotcore-sales-engine/production/MongoDB",
        session_id="tg-live-1-2",
        apply_relational_layer=False,
    )
    assert "pending verification request" in result.reply
    assert "MongoDB" in result.reply
    assert result.meta.get("route_id") == "post_mutation_verification"
