# SPDX-License-Identifier: Apache-2.0
"""Live verification after session reset."""

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


def _seed_execution_job(*, session_id: str = "session-a") -> str:
    pf = authority.create_job(
        title="Restart MongoDB",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "MongoDB",
            "target": {
                "service_name": "MongoDB",
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
            },
            "preflight_status": "ready_for_mutation_approval",
            "preflight_match_key": "railway:restart:mongodb",
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
            "target_name": "MongoDB",
            "target": {
                "service_name": "MongoDB",
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
            "preflight_match_key": "railway:restart:mongodb",
            "provider_evidence_bundle": {"log_summary": "wiredtiger startup activity"},
        },
        session_id=session_id,
        auto_run=False,
    )
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


def test_restart_in_session_a_verify_health_in_session_b() -> None:
    _seed_execution_job(session_id="session-a")
    reset_operation_state_store_for_tests()

    with patch(
        "aethos_core.chat.handlers.runtime_status_reply",
        return_value="GENERIC SYSTEM HEALTH",
    ):
        result = resolve_chat_turn("verify health", session_id="session-b", apply_relational_layer=False)

    assert result.intent == "post_mutation_verify_health"
    assert "MongoDB" in result.reply
    assert "GENERIC SYSTEM HEALTH" not in result.reply
    assert result.meta.get("route_id") == "post_mutation_verification"


def test_no_old_target_resolver_for_path_reply() -> None:
    _seed_execution_job(session_id="session-a")
    reset_operation_state_store_for_tests()

    with patch(
        "aethos_core.chat.mutation_target_chat.compose_target_update_reply",
        return_value=("OLD TARGET RESOLVER", "mutation_target_update", {}),
    ):
        result = resolve_chat_turn(
            "pilotcore-sales-engine/production/MongoDB",
            session_id="session-b",
            apply_relational_layer=False,
        )

    assert "OLD TARGET RESOLVER" not in result.reply
    assert "latest **restart** lifecycle" in result.reply
