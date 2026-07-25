# SPDX-License-Identifier: Apache-2.0
"""Railway restart diagnostics and adapter semantics tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.hardening.restart_transition import LOG_RESTART_DETECTED, verify_railway_restart_transition
from aethos_core.providers.railway.mutations import restart_railway_service
from aethos_core.providers.railway.operations.mutation_adapter import RailwayMutationAdapter
from aethos_core.providers.railway.restart_diagnostics import diagnose_railway_mutation_target
from aethos_core.providers.railway.target_resolver import ProviderTarget


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _target() -> ProviderTarget:
    return ProviderTarget(
        provider="railway",
        service_name="atlas-trader api",
        service_id="svc-123",
        project_name="atlas-trader",
        environment="production",
        resolved=True,
        confidence=0.95,
    )


def test_diagnose_plans_service_instance_redeploy_with_full_ids():
    token = "token"
    target = _target()
    with patch(
        "aethos_core.providers.railway.api_client.find_service_by_name",
        return_value={
            "service_id": "svc-123",
            "service_name": "atlas-trader api",
            "project_id": "proj-1",
            "project_name": "atlas-trader",
        },
    ), patch(
        "aethos_core.providers.railway.operations.mutations_api.resolve_environment_id",
        return_value={"environment_id": "env-prod", "environment_name": "production"},
    ), patch(
        "aethos_core.providers.railway.api_client.list_service_deployments",
        return_value=[{"id": "dep-old", "state": "running", "created_at": "2026-01-01T00:00:00+00:00"}],
    ):
        diagnostics = diagnose_railway_mutation_target(token, target=target, operation="restart")

    assert diagnostics.ok is True
    assert diagnostics.service_id == "svc-123"
    assert diagnostics.project_id == "proj-1"
    assert diagnostics.environment_id == "env-prod"
    assert diagnostics.deployment_id == "dep-old"
    assert diagnostics.planned_graphql_operation == "serviceInstanceRedeploy"
    assert diagnostics.planned_mutation_variables == {
        "environmentId": "env-prod",
        "serviceId": "svc-123",
    }


def test_restart_uses_service_instance_redeploy_and_requires_command_confirmation():
    target = _target()
    diagnostics = {
        "ok": True,
        "service_id": "svc-123",
        "service_name": "atlas-trader api",
        "project_id": "proj-1",
        "project_name": "atlas-trader",
        "environment_id": "env-prod",
        "environment_name": "production",
        "deployment_id": "dep-old",
        "planned_graphql_operation": "serviceInstanceRedeploy",
        "planned_mutation_variables": {"environmentId": "env-prod", "serviceId": "svc-123"},
    }
    with patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=("token", "env", None),
    ), patch(
        "aethos_core.providers.railway.restart_diagnostics.diagnose_railway_mutation_target",
        return_value=type("D", (), {"ok": True, "to_dict": lambda self: diagnostics, **diagnostics})(),
    ), patch(
        "aethos_core.providers.railway.operations.mutations_api.submit_service_instance_redeploy",
        return_value={
            "restart_command_submitted": True,
            "provider_request_id": "dep-new",
            "railway_response": {"serviceInstanceRedeploy": "dep-new"},
            "mutation_variables": {"environmentId": "env-prod", "serviceId": "svc-123"},
        },
    ), patch(
        "aethos_core.providers.railway.api_client.fetch_deployment_logs",
        return_value=[{"timestamp": "2026-01-01T00:00:00+00:00", "message": "boot"}],
    ), patch(
        "aethos_core.providers.railway.api_client.list_service_deployments",
        return_value=[{"id": "dep-old", "state": "running", "created_at": "2026-01-01T00:00:00+00:00"}],
    ), patch(
        "aethos_core.providers.railway.hardening.restart_transition.capture_railway_deployment_snapshot",
        side_effect=lambda *_args, **_kwargs: type(
            "S",
            (),
            {"to_dict": lambda self: {"service_id": "svc-123", "latest_deployment_id": "dep-old", "captured_at": "t"}},
        )(),
    ), patch(
        "aethos_core.providers.railway.hardening.restart_transition.snapshot_from_deployments",
        side_effect=lambda _sid, deps, captured_at: type(
            "S",
            (),
            {"to_dict": lambda self: {"service_id": "svc-123", "latest_deployment_id": deps[0]["id"], "captured_at": captured_at}},
        )(),
    ):
        result = restart_railway_service(target=target, request_id="job-test")
        provider = result.as_provider_result()

    assert provider["restart_command_submitted"] is True
    assert provider["graphql_operation"] == "serviceInstanceRedeploy"
    assert provider["environment_id"] == "env-prod"
    assert provider["project_id"] == "proj-1"
    assert provider["ok"] is True


def test_restart_not_confirmed_when_graphql_returns_no_command():
    target = _target()
    diagnostics_obj = diagnose_railway_mutation_target("token", target=target)
    diagnostics_obj.ok = True
    diagnostics_obj.service_id = "svc-123"
    diagnostics_obj.service_name = "atlas-trader api"
    diagnostics_obj.project_id = "proj-1"
    diagnostics_obj.environment_id = "env-prod"
    diagnostics_obj.deployment_id = "dep-old"
    with patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=("token", "env", None),
    ), patch(
        "aethos_core.providers.railway.restart_diagnostics.diagnose_railway_mutation_target",
        return_value=diagnostics_obj,
    ), patch(
        "aethos_core.providers.railway.operations.mutations_api.submit_service_instance_redeploy",
        return_value={
            "restart_command_submitted": False,
            "detail": "permission denied",
            "graphql_ok": True,
            "railway_response": {"serviceInstanceRedeploy": None},
        },
    ), patch("aethos_core.providers.railway.api_client.fetch_deployment_logs", return_value=[]), patch(
        "aethos_core.providers.railway.api_client.list_service_deployments",
        return_value=[{"id": "dep-old", "state": "running", "created_at": "2026-01-01T00:00:00+00:00"}],
    ), patch(
        "aethos_core.providers.railway.hardening.restart_transition.capture_railway_deployment_snapshot",
        side_effect=lambda *_args, **_kwargs: type(
            "S",
            (),
            {"to_dict": lambda self: {"service_id": "svc-123", "latest_deployment_id": "dep-old", "captured_at": "t"}},
        )(),
    ), patch(
        "aethos_core.providers.railway.hardening.restart_transition.snapshot_from_deployments",
        side_effect=lambda _sid, deps, captured_at: type(
            "S",
            (),
            {"to_dict": lambda self: {"service_id": "svc-123", "latest_deployment_id": deps[0]["id"], "captured_at": captured_at}},
        )(),
    ):
        provider = restart_railway_service(target=target, request_id="job-test").as_provider_result()

    assert provider["ok"] is False
    assert provider["restart_command_submitted"] is False


def test_log_restart_detected_when_deployment_unchanged():
    before = {
        "service_id": "svc-123",
        "active_deployment_id": "dep-old",
        "active_deployment_created_at": "2026-01-01T00:00:00+00:00",
        "latest_deployment_id": "dep-old",
        "latest_deployment_status": "running",
        "captured_at": "2026-01-15T12:00:00+00:00",
    }
    after = dict(before)
    result = verify_railway_restart_transition(
        service_id="svc-123",
        before_snapshot=before,
        approved_at="2026-01-15T12:00:00+00:00",
        after_snapshot=after,
        provider_result={
            "restart_command_submitted": True,
            "ok": True,
            "rollback_metadata": {
                "logs_before_latest_timestamp": "2026-01-01T00:00:00+00:00",
                "logs_after_latest_timestamp": "2026-01-15T12:05:00+00:00",
            },
        },
        readonly_artifact={"summary": "Deployment running and healthy"},
        provider_request_accepted=True,
    )
    assert result.state == LOG_RESTART_DETECTED
    assert result.verified is True
    assert result.transition_proof == "logs"


def test_mutation_adapter_dry_run_returns_diagnostics():
    adapter = RailwayMutationAdapter()
    with patch(
        "aethos_core.providers.railway.operations.mutation_adapter.resolve_railway_mutation_credentials",
        return_value=("token", "env", None),
    ), patch(
        "aethos_core.providers.railway.operations.mutation_adapter.diagnose_railway_mutation_target",
        return_value=type(
            "D",
            (),
            {
                "ok": True,
                "issues": [],
                "to_dict": lambda self: {"planned_graphql_operation": "serviceInstanceRedeploy", "service_id": "svc-123"},
            },
        )(),
    ):
        out = adapter.dry_run(operation="restart", params={"target_name": "atlas-trader api"})
    assert out["dry_run"] is True
    assert "serviceInstanceRedeploy" in out["detail"]
    assert out["mutation_diagnostics"]["service_id"] == "svc-123"
