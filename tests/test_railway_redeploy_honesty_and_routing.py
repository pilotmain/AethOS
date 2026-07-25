# SPDX-License-Identifier: Apache-2.0
"""Regression tests for honest redeploy claims, staging execution, and follow-up routing."""

from __future__ import annotations

from time import time
from unittest.mock import patch

import pytest

from aethos_core.operation_lifecycle.lifecycle_followup_router import compose_lifecycle_followup_reply
from aethos_core.operation_lifecycle.lifecycle_resolver import (
    compose_duplicate_mutation_reply,
    has_completed_operation,
    has_recent_mutation_execution,
    is_operation_verified,
)
from aethos_core.operation_lifecycle.operation_state_store import (
    OperationLifecycleState,
    reset_operation_state_store_for_tests,
)
from aethos_core.operations.mutations.lifecycle_authority import STABILIZING_STATE, mutation_summary
from aethos_core.post_mutation_verification.verification_intent_router import (
    clear_pending_verification_request,
    looks_like_verification_target_selection,
    store_pending_verification_disambiguation,
)
from aethos_core.providers.railway.target_resolver import ProviderTarget
from aethos_core.task_frame.railway_redeploy_continuation import compose_railway_redeploy_continuation_reply


@pytest.fixture(autouse=True)
def _reset_state():
    reset_operation_state_store_for_tests()
    clear_pending_verification_request("default")
    yield
    reset_operation_state_store_for_tests()
    clear_pending_verification_request("default")


def _stabilizing_state(*, operation: str = "redeploy") -> OperationLifecycleState:
    now = time()
    return OperationLifecycleState(
        provider="railway",
        project="pilotos",
        environment="staging",
        service="aethos-ui",
        operation=operation,
        execution_job_id="job-exec-1",
        approval_status="approved",
        execution_status="running",
        verification_status="stabilizing",
        canonical_state=STABILIZING_STATE,
        started_at=now - 180,
        completed_at=now - 60,
        latest_summary=f"Mutation {operation} on aethos-ui · {operation} requested · stabilizing",
        session_id="default",
        match_key=f"railway:{operation}:aethos-ui",
        updated_at=now - 60,
    )


def test_stabilizing_state_is_not_completed_success():
    state = _stabilizing_state()
    assert has_recent_mutation_execution(state)
    assert not is_operation_verified(state)
    assert not has_completed_operation(state)


def test_duplicate_reply_is_honest_when_unverified():
    reply = compose_duplicate_mutation_reply(_stabilizing_state())
    assert "not confirmed yet" in reply.lower()
    assert "successfully" not in reply.lower()


def test_update_please_reports_honest_status():
    from aethos_core.operation_lifecycle.operation_state_store import upsert_operation_state

    upsert_operation_state(_stabilizing_state())
    reply = compose_lifecycle_followup_reply("update please", session_id="default")
    assert reply is not None
    text, intent, _meta = reply
    assert intent == "operation_lifecycle_completion_status"
    assert "not confirmed yet" in text.lower() or "verification is still running" in text.lower()
    assert "successfully" not in text.lower()


def test_redeploy_summary_uses_redeploy_requested_language():
    summary = mutation_summary(
        provider="railway",
        operation_type="redeploy",
        target="aethos-api",
        canonical_state=STABILIZING_STATE,
    )
    assert "redeploy requested" in summary
    assert "restart requested" not in summary


def test_redeploy_service_uses_staging_environment():
    from aethos_core.providers.railway.operations.mutations_api import redeploy_service

    with patch(
        "aethos_core.providers.railway.operations.mutations_api._resolve_service",
        return_value={"service_id": "svc-1", "service_name": "aethos-api", "project_id": "proj-1"},
    ), patch(
        "aethos_core.providers.railway.operations.mutations_api.resolve_environment_id",
        return_value={"environment_id": "env-staging", "environment_name": "staging"},
    ) as resolve_env, patch(
        "aethos_core.providers.railway.operations.mutations_api.submit_service_instance_redeploy",
        return_value={"ok": True, "restart_command_submitted": True, "provider_request_id": "req-1"},
    ) as submit:
        result = redeploy_service(
            "token",
            target_name="aethos-api",
            environment_name="staging",
        )
        assert result["ok"] is True
        resolve_env.assert_called_once_with("token", project_id="proj-1", preferred_name="staging")
        submit.assert_called_once_with("token", environment_id="env-staging", service_id="svc-1")


def test_restart_railway_service_passes_redeploy_operation_to_diagnostics():
    from aethos_core.providers.railway.mutations import restart_railway_service

    target = ProviderTarget(
        provider="railway",
        service_name="aethos-api",
        project_name="pilotos",
        environment="staging",
        resolved=True,
    )
    from aethos_core.providers.railway.restart_diagnostics import RailwayMutationDiagnostics

    diag = RailwayMutationDiagnostics(
        ok=True,
        service_id="svc-1",
        service_name="aethos-api",
        project_id="proj-1",
        environment_id="env-staging",
        deployment_id="dep-1",
        governed_operation="redeploy",
    )

    with patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=("token", "env", None),
    ), patch(
        "aethos_core.providers.railway.restart_diagnostics.diagnose_railway_mutation_target",
        return_value=diag,
    ) as diagnose, patch(
        "aethos_core.providers.railway.hardening.restart_transition.capture_railway_deployment_snapshot",
        return_value=type("Snap", (), {"to_dict": lambda self: {}})(),
    ), patch(
        "aethos_core.providers.railway.api_client.list_service_deployments",
        return_value=[{"id": "dep-1", "state": "success", "created_at": "2026-01-01T00:00:00Z"}],
    ), patch(
        "aethos_core.providers.railway.operations.mutations_api.submit_service_instance_redeploy",
        return_value={"restart_command_submitted": True, "provider_request_id": "req-1"},
    ), patch(
        "aethos_core.providers.railway.api_client.fetch_deployment_logs",
        return_value=[],
    ), patch(
        "aethos_core.providers.railway.mutations.get_settings",
    ) as settings:
        settings.return_value.railway_restart_provider_operation = "service_instance_redeploy"
        result = restart_railway_service(target=target, request_id="req-1", operation="redeploy")
        assert result.operation == "redeploy"
        assert diagnose.call_args.kwargs["operation"] == "redeploy"


def test_numbered_verification_selection_does_not_create_redeploy_preflights():
    store_pending_verification_disambiguation(
        session_id="default",
        intent="verify_health",
        original_text="yes please verify health and latest logs",
        candidates=[_stabilizing_state(), _stabilizing_state(operation="redeploy")],
    )
    pasted = (
        "1. **pilotos / staging / aethos-ui** — redeploy\n"
        "2. **pilotos / staging / aethos-api** — redeploy"
    )
    assert looks_like_verification_target_selection(pasted)
    routed = compose_railway_redeploy_continuation_reply(pasted, session_id="default")
    assert routed is None
