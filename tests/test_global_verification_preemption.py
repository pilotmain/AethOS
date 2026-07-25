# SPDX-License-Identifier: Apache-2.0
"""Global post-mutation verification preemption tests."""

from __future__ import annotations

import pytest

from aethos_core.chat.front_door_intent import classify_front_door_intent
from aethos_core.conversation.provider_memory.active_provider_context import is_provider_neutral_health_phrase
from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import (
    reset_operation_state_store_for_tests,
    upsert_operation_state_from_job,
)
from aethos_core.operations.mutations.lifecycle_authority import EXECUTION_COMPLETED_STATE
from aethos_core.post_mutation_verification.global_verification_preemption import (
    is_global_verification_query,
    route_global_verification_query,
    should_preempt_to_post_mutation_verification,
    verification_preemption_blocks_route,
)
from aethos_core.post_mutation_verification.verification_intent_router import (
    reset_pending_verification_for_tests,
    store_pending_verification_request,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store
from aethos_core.world_model.world_model_followup_router import classify_world_model_followup


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


def test_verify_health_preempts_system_health() -> None:
    _seed_execution_job()
    assert should_preempt_to_post_mutation_verification("verify health", session_id="default")
    assert not is_provider_neutral_health_phrase("verify health", session_id="default")
    routed = route_global_verification_query("verify health", session_id="default")
    assert routed is not None
    assert "MongoDB" in routed.reply
    assert routed.meta.get("route_id") == "post_mutation_verification"


def test_top_5_logs_preempts_capability_intro() -> None:
    _seed_execution_job()
    prompt = "can you check top 5 logs to see if application started?"
    assert is_global_verification_query(prompt, session_id="default")
    assert classify_front_door_intent(prompt, session_id="default") != "capability_intro"
    routed = route_global_verification_query(prompt, session_id="default")
    assert routed is not None
    assert routed.intent == "post_mutation_startup_log_check"


def test_what_changed_after_restart_preempts_world_model() -> None:
    _seed_execution_job()
    prompt = "what changed after restart?"
    assert verification_preemption_blocks_route(prompt, session_id="default")
    assert classify_world_model_followup(prompt, session_id="default") is None
    routed = route_global_verification_query(prompt, session_id="default")
    assert routed is not None
    assert "MongoDB" in routed.reply


def test_fetch_logs_after_restart_preempts_provider_followup() -> None:
    _seed_execution_job(session_id="tg-123-456")
    prompt = "fetch logs after restart"
    assert should_preempt_to_post_mutation_verification(prompt, session_id="tg-123-456")
    routed = route_global_verification_query(prompt, session_id="tg-123-456")
    assert routed is not None
    assert "MongoDB" in routed.reply


def test_explicit_path_continues_pending_verification() -> None:
    _seed_execution_job()
    store_pending_verification_request(
        session_id="default",
        intent="startup_log_check",
        original_text="can you check top 5 logs to see if application started?",
    )
    routed = route_global_verification_query(
        "pilotcore-sales-engine/production/MongoDB",
        session_id="default",
    )
    assert routed is not None
    assert "pending verification request" in routed.reply
    assert "MongoDB" in routed.reply
