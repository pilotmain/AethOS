# SPDX-License-Identifier: Apache-2.0
"""Verification context discovery tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.conversation.provider_memory.active_provider_context import is_provider_neutral_health_phrase
from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import (
    reset_operation_state_store_for_tests,
    upsert_operation_state_from_job,
)
from aethos_core.operations.mutations.lifecycle_authority import EXECUTION_COMPLETED_STATE
from aethos_core.post_mutation_verification.verification_context_discovery import (
    discover_verification_lifecycle,
    global_mutation_lifecycle_exists,
)
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


def test_verify_health_uses_global_index_when_session_empty() -> None:
    _seed_execution_job(session_id="session-a")
    reset_operation_state_store_for_tests()
    discovered = discover_verification_lifecycle("verify health", session_id="fresh-session")
    assert discovered is not None
    assert discovered.service == "MongoDB"
    reply = route_post_mutation_verification("verify health", session_id="fresh-session")
    assert reply is not None
    assert "MongoDB" in reply[0]
    assert "latest mutation I found" in reply[0]


def test_fetch_logs_after_restart_uses_global_index() -> None:
    _seed_execution_job(session_id="session-a")
    reset_operation_state_store_for_tests()
    reply = route_post_mutation_verification("fetch logs after restart", session_id="fresh-session")
    assert reply is not None
    assert "MongoDB" in reply[0]


def test_path_reply_resolves_lifecycle_by_target() -> None:
    _seed_execution_job(session_id="session-a")
    reset_operation_state_store_for_tests()
    reply = route_post_mutation_verification(
        "pilotcore-sales-engine/production/MongoDB",
        session_id="fresh-session",
    )
    assert reply is not None
    assert "latest **restart** lifecycle" in reply[0]
    assert "verify health" in reply[0]


def test_system_health_only_wins_when_no_lifecycle_exists() -> None:
    assert global_mutation_lifecycle_exists() is False
    assert is_provider_neutral_health_phrase("verify health", session_id="fresh-session") is True

    _seed_execution_job(session_id="session-a")
    assert global_mutation_lifecycle_exists() is True
    assert is_provider_neutral_health_phrase("verify health", session_id="fresh-session") is False
    assert is_provider_neutral_health_phrase("AethOS system health", session_id="fresh-session") is True


def test_restart_not_treated_as_service_in_verification_context() -> None:
    _seed_execution_job(session_id="session-a")
    reset_operation_state_store_for_tests()
    discovered = discover_verification_lifecycle("what changed after restart?", session_id="fresh-session")
    assert discovered is not None
    assert discovered.service == "MongoDB"
    assert discovered.service != "restart"
