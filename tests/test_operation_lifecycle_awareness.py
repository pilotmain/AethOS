# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from time import time
from unittest.mock import patch

import pytest

from aethos_core.operation_lifecycle.lifecycle_followup_router import compose_lifecycle_followup_reply
from aethos_core.operation_lifecycle.lifecycle_resolver import (
    compose_duplicate_mutation_reply,
    get_latest_operation_state,
    has_completed_operation,
    has_recent_mutation_execution,
    is_duplicate_mutation_request,
)
from aethos_core.operation_lifecycle.operation_state_store import (
    OperationLifecycleState,
    reset_operation_state_store_for_tests,
    upsert_operation_state,
)
from aethos_core.operations.mutations.lifecycle_authority import EXECUTION_COMPLETED_STATE, VERIFIED_STATE
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store
from tests.job_test_utils import drain_job_executor


@pytest.fixture(autouse=True)
def _reset_lifecycle_store():
    reset_operation_state_store_for_tests()
    yield
    reset_operation_state_store_for_tests()


def _completed_execution_job(*, session_id: str = "default", service: str = "MongoDB") -> str:
    pf = authority.create_job(
        title="Restart MongoDB",
        job_type="mutation_preflight",
        params={
            "user_request": "restart MongoDB on Railway",
            "provider": "railway",
            "operation_type": "restart",
            "target_name": service,
            "target_resolved": True,
            "target": {
                "service_name": service,
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
                "resolved": True,
            },
            "preflight_status": "ready_for_mutation_approval",
            "preflight_match_key": f"railway:restart:{service.lower()}",
            "mutation_execution_approved": True,
            "is_current": True,
        },
        session_id=session_id,
        auto_run=False,
    )
    job_store.complete_with_result(
        pf.id,
        full_result="preflight done",
        summary="preflight done",
        preview="preflight",
        provider="mutation_preflight",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )

    exec_job = authority.create_job(
        title="Restart MongoDB execution",
        job_type="mutation_execution",
        params={
            "user_request": "restart MongoDB on Railway",
            "provider": "railway",
            "operation_type": "restart",
            "target_name": service,
            "target": {
                "service_name": service,
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
                "resolved": True,
            },
            "preflight_job_id": pf.id,
            "source_mutation_preflight_job_id": pf.id,
            "executed": True,
            "execution_state": "execution_completed",
            "verification_state": "verification_running",
            "canonical_lifecycle_state": EXECUTION_COMPLETED_STATE,
            "lifecycle_summary": "Mutation restart on MongoDB · execution completed · verification running",
            "mutation_execution_approved": True,
            "preflight_match_key": f"railway:restart:{service.lower()}",
        },
        session_id=session_id,
        auto_run=False,
    )
    pf_job = job_store.get(pf.id)
    if pf_job:
        pf_job.params["mutation_execution_job_id"] = exec_job.id
        pf_job.params["mutation_execution_approved"] = True
    job_store.complete_with_result(
        exec_job.id,
        full_result="execution done",
        summary="execution done",
        preview="execution",
        provider="mutation_execution",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )
    return exec_job.id


def _credential_blocked_preflight(*, session_id: str = "default") -> str:
    with patch(
        "aethos_core.operations.mutations.preflight._mutation_provider_auth_block",
        return_value="needs_credential",
    ):
        job = authority.create_job(
            title="Restart MongoDB",
            job_type="mutation_preflight",
            params={
                "user_request": "restart MongoDB on Railway",
                "provider": "railway",
                "operation_type": "restart",
                "target_name": "MongoDB",
                "target_resolved": True,
                "target": {
                    "service_name": "MongoDB",
                    "project_name": "pilotcore-sales-engine",
                    "environment": "production",
                    "resolved": True,
                },
            },
            session_id=session_id,
            auto_run=True,
        )
        drain_job_executor()
    return job.id


def test_successful_restart_prevents_duplicate_preflight():
    _completed_execution_job()

    duplicate, state = is_duplicate_mutation_request("restart MongoDB", session_id="default")
    assert duplicate is True
    assert state is not None
    assert state.service == "MongoDB"

    from aethos_core.chat.explicit_mutation_intent import compose_explicit_mutation_preflight_reply

    reply = compose_explicit_mutation_preflight_reply("restart MongoDB", session_id="default")
    assert reply is not None
    assert "already" in reply[0].lower()
    assert reply[1] == "operation_lifecycle_duplicate_blocked"


def test_why_cant_approve_after_success():
    _completed_execution_job()

    reply = compose_lifecycle_followup_reply("why can't I approve?", session_id="default")
    assert reply is not None
    text, intent, _meta = reply
    assert intent == "operation_lifecycle_completed_context"
    assert "do not need to approve" in text.lower() or "already completed" in text.lower()
    assert "credential" not in text.lower() or "no credential is currently blocking" in text.lower()


def test_what_credential_missing_after_success():
    _completed_execution_job()

    reply = compose_lifecycle_followup_reply("what credential is missing?", session_id="default")
    assert reply is not None
    text, intent, _meta = reply
    assert intent == "operation_lifecycle_completed_context"
    assert "No credential is currently blocking" in text


def test_restart_again_explicit_override():
    _completed_execution_job()

    duplicate, _state = is_duplicate_mutation_request("restart MongoDB again", session_id="default")
    assert duplicate is False


def test_completed_lifecycle_survives_route_changes():
    exec_id = _completed_execution_job()
    state = get_latest_operation_state(session_id="default", service="MongoDB")
    assert state is not None
    assert state.execution_job_id == exec_id
    assert has_recent_mutation_execution(state)
    assert not has_completed_operation(state)


def test_lifecycle_followups_beat_crash_fallback(monkeypatch):
    _completed_execution_job()

    def _boom(*_args, **_kwargs):
        raise RuntimeError("world model crash")

    monkeypatch.setattr(
        "aethos_core.world_model.safe_world_model_runtime.safe_route_world_model_followup",
        _boom,
    )

    from aethos_core.capabilities.capability_executor import execute_cognition_strategy
    from aethos_core.operational_cognition.types import OperationalCognitionDecision

    decision = OperationalCognitionDecision(
        intent="general_operational",
        provider="railway",
        target="MongoDB",
        scope="session",
        capabilities=["railway"],
        confidence=0.9,
    )
    result = execute_cognition_strategy(decision, "why can't I approve?", session_id="default")
    assert result.handled is True
    assert result.route_id == "operation_lifecycle"
    assert "credential" not in result.reply.lower() or "no credential is currently blocking" in result.reply.lower()


def test_credential_guidance_only_when_blocked():
    _credential_blocked_preflight(session_id="cred-blocked-session")

    reply = compose_lifecycle_followup_reply(
        "what credential is missing?",
        session_id="cred-blocked-session",
    )
    assert reply is not None
    text, intent, _meta = reply
    assert intent == "credential_requirement_guidance"
    assert "RAILWAY_API_TOKEN" in text


def test_operation_state_store_roundtrip():
    state = OperationLifecycleState(
        provider="railway",
        project="pilotcore-sales-engine",
        environment="production",
        service="MongoDB",
        operation="restart",
        preflight_job_id="job-abc",
        execution_job_id="job-def",
        approval_status="approved",
        execution_status="completed",
        verification_status="stabilizing",
        canonical_state=VERIFIED_STATE,
        started_at=time() - 120,
        completed_at=time() - 60,
        credential_blocked=False,
        latest_summary="verified healthy",
        session_id="default",
        match_key="railway:restart:mongodb",
    )
    upsert_operation_state(state)
    loaded = get_latest_operation_state(session_id="default", service="MongoDB")
    assert loaded is not None
    assert loaded.execution_job_id == "job-def"
    assert loaded.verification_status == "stabilizing"
