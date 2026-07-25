# SPDX-License-Identifier: Apache-2.0
"""Verification should not duplicate clarification for same logical target."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import (
    reset_operation_state_store_for_tests,
    upsert_operation_state_from_job,
)
from aethos_core.operations.mutations.lifecycle_authority import EXECUTION_COMPLETED_STATE
from aethos_core.post_mutation_verification.verification_intent_router import (
    reset_pending_verification_for_tests,
    route_post_mutation_verification,
)
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


def _seed_execution_job(*, suffix: str) -> str:
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
        session_id="session-a",
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
            "canonical_lifecycle_state": EXECUTION_COMPLETED_STATE,
            "lifecycle_summary": "Mutation restart on MongoDB",
            "preflight_match_key": "railway:restart:mongodb",
            "provider_evidence_bundle": {"log_summary": "wiredtiger startup activity"},
        },
        session_id="session-a",
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
    job = job_store.get(exec_job.id)
    if job:
        job.updated_at = float(len(suffix) + 1)
    upsert_operation_state_from_job(job)
    return exec_job.id


@pytest.mark.parametrize(
    "prompt,intent_fragment",
    [
        ("verify health", "post_mutation_verify_health"),
        ("fetch logs after restart", "post_mutation_fetch_logs"),
        ("what changed after restart?", "post_mutation_what_changed"),
    ],
)
def test_auto_select_if_only_logical_candidate(prompt: str, intent_fragment: str) -> None:
    _seed_execution_job(suffix="a")
    _seed_execution_job(suffix="b")
    _seed_execution_job(suffix="c")
    reply = route_post_mutation_verification(prompt, session_id="fresh-session")
    assert reply is not None
    assert reply[1] == intent_fragment
    assert "Which recent operation should I use?" not in reply[0]
    assert "multiple recent mutation operations" not in reply[0]


def test_live_verify_health_auto_selects() -> None:
    _seed_execution_job(suffix="a")
    _seed_execution_job(suffix="b")
    reset_operation_state_store_for_tests()
    result = resolve_chat_turn("verify health", session_id="fresh-session", apply_relational_layer=False)
    assert result.intent == "post_mutation_verify_health"
    assert "Which recent operation should I use?" not in result.reply
