# SPDX-License-Identifier: Apache-2.0
"""Railway governed mutation execution."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.operations.mutations.execution import run_mutation_execution
from aethos_core.operations.mutations.lifecycle import EXECUTION_FAILED, EXECUTION_MUTATION_REQUESTED, EXECUTION_STABILIZING
from aethos_core.operations.mutations.mutation_execution_flow import approve_mutation_execution
from aethos_core.providers.railway.mutations import RailwayMutationResult, restart_railway_service
from aethos_core.providers.railway.target_resolver import ProviderTarget
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _mutation_enabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()


def _seed_ready_preflight() -> str:
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "atlas-trader api",
            "target_resolved": True,
            "target": {
                "provider": "railway",
                "service_name": "atlas-trader api",
                "service_id": "svc-123",
                "project_name": "atlas-trader",
                "environment": "production",
                "resolved": True,
                "confidence": 0.95,
            },
            "preflight_status": "ready_for_mutation_approval",
            "risk_tier": "T2_low_risk_mutation",
            "rollback_plan": {"strategy": "redeploy_previous"},
            "blast_radius": {"scope": "single_service"},
            "user_request": "Restart Railway atlas-trader api service",
        },
        source="test",
        session_id="rail-exec",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    stored.params["mutation_preflight"] = {
        "provider": "railway",
        "operation_type": "restart",
        "target_name": "atlas-trader api",
        "target_resolved": True,
        "preflight_status": "ready_for_mutation_approval",
        "risk_tier": "T2_low_risk_mutation",
    }
    stored.params["is_current"] = True
    return job.id


def test_restart_railway_service_missing_credentials():
    with patch("aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials", return_value=(None, "missing", "Railway mutation credentials are not configured.")):
        result = restart_railway_service(
            target=ProviderTarget(provider="railway", service_name="atlas-trader api", service_id="svc-123", resolved=True),
            request_id="job-test",
        )
    assert result.success is False
    assert "credential" in (result.error or "").lower()


def test_approved_railway_restart_calls_restart_adapter():
    preflight_id = _seed_ready_preflight()
    accepted = RailwayMutationResult(
        provider="railway",
        operation="restart",
        target_name="atlas-trader api",
        target_id="svc-123",
        success=True,
        provider_request_id="dep-1",
        deployment_id="dep-1",
        raw_response={"serviceInstanceRedeploy": "dep-1"},
        executed_at="2026-01-01T00:00:00+00:00",
    )
    accepted.restart_command_submitted = True
    accepted.graphql_operation = "serviceInstanceRedeploy"
    with patch(
        "aethos_core.providers.railway.mutations.restart_railway_service",
        return_value=accepted,
    ) as restart_mock:
        preflight, execution = approve_mutation_execution(preflight_id)
        job_executor.drain_queue_for_tests()
        job_executor.enqueue(execution.id)
        assert job_executor.drain_once_for_tests()
        restart_mock.assert_called_once()

    stored = job_store.get(execution.id)
    assert stored is not None
    assert stored.params.get("executed") is True
    assert stored.params.get("execution_state") in {EXECUTION_MUTATION_REQUESTED, EXECUTION_STABILIZING}
    assert stored.params.get("execution_state") != "execution_completed"
    assert stored.params.get("verification_job_id")


def test_missing_credentials_marks_execution_failed():
    preflight_id = _seed_ready_preflight()
    with patch(
        "aethos_core.providers.railway.mutations.restart_railway_service",
        return_value=RailwayMutationResult(
            provider="railway",
            operation="restart",
            target_name="atlas-trader api",
            target_id="svc-123",
            success=False,
            provider_request_id=None,
            deployment_id=None,
            error="Railway mutation credentials are not configured.",
            executed_at="2026-01-01T00:00:00+00:00",
        ),
    ):
        _preflight, execution = approve_mutation_execution(preflight_id)
        job_executor.drain_queue_for_tests()
        job_executor.enqueue(execution.id)
        assert job_executor.drain_once_for_tests()

    stored = job_store.get(execution.id)
    assert stored is not None
    assert stored.params.get("executed") is False
    assert stored.params.get("execution_state") == EXECUTION_FAILED


def test_provider_accepted_does_not_mark_execution_completed():
    with patch(
        "aethos_core.providers.railway.operations.mutation_adapter.execute_railway_mutation",
        return_value={
            "ok": True,
            "restart_command_submitted": True,
            "execution_state": "provider_mutation_requested",
            "railway_mutation_result": {"success": True},
            "detail": "Railway restart command submitted for `atlas-trader api`.",
        },
    ):
        outcome = run_mutation_execution(
            params={
                "provider": "railway",
                "operation_type": "restart",
                "target_name": "atlas-trader api",
                "target": {"service_name": "atlas-trader api", "service_id": "svc-123", "resolved": True},
                "mutation_execution_approved": True,
                "risk_tier": "T2_low_risk_mutation",
            },
            job_id="job-exec-state",
        )
    assert outcome.executed is True
    assert outcome.artifact.get("execution_state") == EXECUTION_MUTATION_REQUESTED
    assert outcome.artifact.get("canonical_lifecycle_state") != "execution_completed"


def test_audit_includes_provider_response():
    with patch(
        "aethos_core.providers.railway.operations.mutation_adapter.execute_railway_mutation",
        return_value={
            "ok": True,
            "restart_command_submitted": True,
            "execution_state": "provider_mutation_requested",
            "railway_mutation_result": {"success": True, "deployment_id": "dep-1"},
            "provider_result": {"ok": True},
        },
    ):
        outcome = run_mutation_execution(
            params={
                "provider": "railway",
                "operation_type": "restart",
                "target_name": "atlas-trader api",
                "mutation_execution_approved": True,
                "risk_tier": "T2_low_risk_mutation",
            },
            job_id="job-audit",
        )
    audit = outcome.artifact.get("audit") or {}
    assert audit
    assert outcome.artifact.get("provider_result")
