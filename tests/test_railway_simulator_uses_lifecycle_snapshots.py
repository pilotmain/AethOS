# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 99C — simulator reuses deployment lifecycle readiness snapshots."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aethos_core.providers.railway.deployment_plan.creation_preflight import build_creation_preflight_from_plan
from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    clear_for_tests as clear_preflight,
    save_creation_preflight,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests as clear_plan,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
    clear_for_tests as clear_readiness,
    save_readiness_context,
)
from aethos_core.providers.railway.env_value_readiness.env_value_context import clear_for_tests as clear_env_ctx
from aethos_core.providers.railway.service_creation_simulator.simulator_checks import (
    check_railway_credential_readiness,
    check_railway_project_environment,
    run_all_simulator_checks,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_result import build_simulation_result


def setup_function() -> None:
    clear_plan()
    clear_preflight()
    clear_readiness()
    clear_env_ctx()


def _plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-99c",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["APP_ENV", "API_PORT", "ANTHROPIC_API_KEY"],
            "mutation_ready": True,
        }
    )


def _passed_readiness_checks() -> dict:
    return {
        "inventory": {"ok": True, "error": "", "project_count": 1},
        "github_binding": {"github_credential_ok": True},
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "service_creation": {"api": True},
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "readonly_readiness_ok": True,
    }


def _failing_inventory() -> MagicMock:
    inventory = MagicMock()
    inventory.error = "rate limited"
    inventory.projects = []
    return inventory


@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
def test_project_env_passes_from_snapshot_when_live_inventory_fails(mock_discover) -> None:
    mock_discover.return_value = _failing_inventory()
    plan = _plan()
    save_readiness_context(session_id="snap-99c", checks=_passed_readiness_checks())
    row = check_railway_project_environment(plan=plan, session_id="snap-99c")
    assert row["status"] == "pass"
    assert row["resolution_source"] == "deployment lifecycle readiness snapshot"
    assert row["inventory_probe"]["status"] == "degraded"
    assert row["inventory_probe"]["reason"] == "rate_limited"


@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
@patch("aethos_core.credentials.get_provider_api_token")
def test_credential_passes_when_token_exists_despite_inventory_fail(mock_token, mock_discover) -> None:
    mock_discover.return_value = _failing_inventory()
    mock_token.return_value = "railway-token"
    row = check_railway_credential_readiness()
    assert row["status"] == "pass"
    assert row["canonical_token_present"] is True


@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
@patch("aethos_core.credentials.get_provider_api_token")
def test_blocking_reasons_exclude_project_and_credential_when_snapshot_and_token(
    mock_token,
    mock_discover,
) -> None:
    mock_discover.return_value = _failing_inventory()
    mock_token.return_value = "railway-token"
    plan = _plan()
    session = "block-99c"
    save_readiness_context(session_id=session, checks=_passed_readiness_checks())
    save_deployment_plan_context(session_id=session, plan=plan)
    preflight = build_creation_preflight_from_plan(plan)
    save_creation_preflight(session_id=session, preflight=preflight)

    simulation = build_simulation_result(plan=plan, preflight=preflight, session_id=session)
    blocking = list(simulation["blocking_reasons"])
    assert "project_environment_unresolved" not in blocking
    assert "railway_credential_not_ready" not in blocking
    assert "env_values_not_configured" in blocking or "greenfield_service_creation_not_wired" in blocking


@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
@patch("aethos_core.credentials.get_provider_api_token", return_value="tok")
def test_live_inventory_failure_only_in_diagnostics(mock_token, mock_discover) -> None:
    mock_discover.return_value = _failing_inventory()
    plan = _plan()
    save_readiness_context(session_id="diag-99c", checks=_passed_readiness_checks())
    checks = run_all_simulator_checks(
        plan=plan,
        preflight=build_creation_preflight_from_plan(plan),
        session_id="diag-99c",
    )
    pe = next(r for r in checks if r["check"] == "railway_project_environment")
    assert pe["status"] == "pass"
    assert pe.get("inventory_probe", {}).get("status") == "degraded"

    from aethos_core.providers.railway.service_creation_simulator.simulator_renderer import (
        render_simulation_artifact,
    )

    simulation = build_simulation_result(
        plan=plan,
        preflight=build_creation_preflight_from_plan(plan),
        checks=checks,
        session_id="diag-99c",
    )
    body = render_simulation_artifact(simulation, session_id="diag-99c")
    assert "Diagnostics:" in body
    assert "Inventory probe: degraded" in body
    assert "Project/environment resolution: fail" not in body
