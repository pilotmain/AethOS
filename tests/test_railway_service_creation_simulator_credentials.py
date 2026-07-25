# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 98C — simulator Railway credential readiness aligns with canonical resolver."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_plan.creation_preflight import build_creation_preflight_from_plan
from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    clear_for_tests as clear_preflight,
    save_creation_preflight,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests as clear_lifecycle,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests as clear_plan,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.service_creation_simulator.simulator_checks import (
    check_execution_api_surface,
    check_railway_credential_readiness,
    check_railway_project_environment,
    run_all_simulator_checks,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
    clear_for_tests as clear_sim,
    get_simulation,
    save_simulation,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_normalization import (
    normalize_simulation_snapshot,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_renderer import (
    render_blocking_followup,
    render_simulation_artifact,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_result import (
    build_simulation_result,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)


def setup_function() -> None:
    clear_plan()
    clear_preflight()
    clear_sim()
    clear_lifecycle()


def _confirmed_plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-98c",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["APP_ENV", "OPENAI_API_KEY"],
            "mutation_ready": True,
        }
    )


@patch("aethos_core.credentials.get_provider_api_token")
def test_canonical_token_passes_without_inventory_probe(mock_token) -> None:
    mock_token.return_value = "railway-token-redacted"
    row = check_railway_credential_readiness()
    assert row["status"] == "pass"
    assert row.get("canonical_token_present") is True
    assert row.get("credential_source") == "canonical provider credential resolver"
    assert "inventory" not in row.get("details", "").lower() or "separately" in row.get("details", "").lower()


@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
@patch("aethos_core.credentials.get_provider_api_token")
def test_token_passes_when_project_resolution_fails(mock_token, mock_inventory) -> None:
    mock_token.return_value = "railway-token-redacted"
    mock_inventory.return_value = type(
        "Inv",
        (),
        {"error": "project pilotos not found", "projects": []},
    )()
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)

    cred = check_railway_credential_readiness()
    project = check_railway_project_environment(plan=plan)
    assert cred["status"] == "pass"
    assert project["status"] == "fail"

    checks = run_all_simulator_checks(plan=plan, preflight=preflight)
    simulation = build_simulation_result(plan=plan, preflight=preflight, checks=checks)
    assert "railway_credential_not_ready" not in simulation["blocking_reasons"]
    assert "project_environment_unresolved" in simulation["blocking_reasons"]


@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
@patch("aethos_core.credentials.get_provider_api_token")
def test_token_passes_when_inventory_partial_failure(mock_token, mock_inventory) -> None:
    mock_token.return_value = "railway-token-redacted"
    mock_inventory.return_value = type(
        "Inv",
        (),
        {"error": "partial graphql failure", "projects": []},
    )()
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    checks = run_all_simulator_checks(plan=plan, preflight=preflight)
    cred = next(r for r in checks if r["check"] == "railway_credential_readiness")
    assert cred["status"] == "pass"
    simulation = build_simulation_result(plan=plan, preflight=preflight, checks=checks)
    assert "railway_credential_not_ready" not in simulation["blocking_reasons"]


@patch("aethos_core.credentials.get_provider_api_token")
def test_missing_token_fails_credential_check(mock_token) -> None:
    mock_token.return_value = None
    row = check_railway_credential_readiness()
    assert row["status"] == "fail"
    assert row.get("checked_source") == "canonical provider credential resolver"
    assert "railway-token" not in str(row)
    assert "canonical provider credential resolver" in str(row.get("details") or "").lower()


def test_execution_api_surface_stays_blocked_separately() -> None:
    row = check_execution_api_surface()
    assert row["status"] == "blocked"
    assert row.get("check") == "execution_api_surface"


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_result.run_all_simulator_checks")
def test_simulation_blocking_reasons_exclude_credential_when_token_passes(mock_checks) -> None:
    mock_checks.return_value = [
        {"check": "railway_project_environment", "status": "pass"},
        {"check": "service_name_availability", "status": "pass"},
        {"check": "github_source_binding", "status": "pass"},
        {
            "check": "railway_credential_readiness",
            "status": "pass",
            "credential_source": "canonical provider credential resolver",
        },
        {
            "check": "required_env_var_readiness",
            "status": "blocked",
            "env_var_names_status": "pass",
            "env_var_values_status": "blocked",
        },
        {"check": "build_start_health_readiness", "status": "pass"},
        {"check": "rollback_readiness", "status": "pass"},
        {"check": "execution_api_surface", "status": "blocked"},
    ]
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    simulation = build_simulation_result(plan=plan, preflight=preflight, checks=mock_checks.return_value)
    assert "railway_credential_not_ready" not in simulation["blocking_reasons"]
    assert "env_values_not_configured" in simulation["blocking_reasons"]
    assert "greenfield_service_creation_not_wired" in simulation["blocking_reasons"]

    body = render_blocking_followup(simulation)
    assert "Railway credential or readonly inventory is not ready" not in body
    assert "env var values" in body.lower()
    assert "not wired" in body.lower()


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_result.run_all_simulator_checks")
def test_artifact_shows_credential_source_not_token(mock_checks) -> None:
    mock_checks.return_value = [
        {
            "check": "railway_credential_readiness",
            "status": "pass",
            "credential_source": "canonical provider credential resolver",
            "details": "Canonical Railway token is available.",
        },
        {"check": "execution_api_surface", "status": "blocked", "surfaces": {"create_railway_service": "not_wired"}},
    ]
    plan = _confirmed_plan()
    simulation = build_simulation_result(
        plan=plan,
        preflight=build_creation_preflight_from_plan(plan),
        checks=mock_checks.return_value,
    )
    body = render_simulation_artifact(simulation)
    assert "canonical provider credential resolver" in body
    assert "railway-token" not in body
    assert "RAILWAY_API_TOKEN=" not in body


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_result.run_all_simulator_checks")
def test_full_route_blocking_followup_no_credential_blocker(mock_checks) -> None:
    mock_checks.return_value = [
        {"check": "railway_project_environment", "status": "pass"},
        {"check": "service_name_availability", "status": "pass"},
        {"check": "github_source_binding", "status": "pass"},
        {
            "check": "railway_credential_readiness",
            "status": "pass",
            "credential_source": "canonical provider credential resolver",
            "canonical_token_present": True,
        },
        {
            "check": "required_env_var_readiness",
            "status": "blocked",
            "env_var_names_status": "pass",
            "env_var_values_status": "blocked",
        },
        {"check": "build_start_health_readiness", "status": "pass"},
        {"check": "rollback_readiness", "status": "pass"},
        {"check": "execution_api_surface", "status": "blocked"},
    ]
    plan = _confirmed_plan()
    save_deployment_plan_context(session_id="98c-route", plan=plan)
    save_creation_preflight(session_id="98c-route", preflight=build_creation_preflight_from_plan(plan))
    route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="98c-route",
    )
    result = route_railway_service_creation_simulator(
        "what is blocking execution?",
        session_id="98c-route",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_service_creation_simulation_blocking"
    assert "Railway credential or readonly inventory is not ready" not in body
    assert "greenfield" in body.lower() or "not wired" in body.lower()
    assert "env var values" in body.lower()
    stored = get_simulation(session_id="98c-route")
    assert stored is not None
    assert "railway_credential_not_ready" not in stored.get("blocking_reasons", [])


@patch("aethos_core.credentials.get_provider_api_token")
def test_stale_persisted_credential_blocker_removed_when_token_exists(mock_token) -> None:
    mock_token.return_value = "railway-token-redacted"
    stale = {
        "simulation_id": "rsim-stale-98i",
        "repo": "pilotmain/aethos",
        "blocking_reasons": [
            "railway_credential_not_ready",
            "env_values_not_configured",
            "greenfield_service_creation_not_wired",
        ],
        "blocking_reason_messages": [
            "Railway credential or readonly inventory is not ready.",
            "Required env var values have not been supplied through a secure credential path.",
            "Railway greenfield service creation mutation is not wired yet.",
        ],
        "checks": [
            {
                "check": "railway_credential_readiness",
                "status": "fail",
                "details": "inventory probe failed",
            },
            {"check": "execution_api_surface", "status": "blocked"},
        ],
    }
    save_simulation(session_id="98i-stale", simulation=stale)
    loaded = get_simulation(session_id="98i-stale")
    assert loaded is not None
    assert "railway_credential_not_ready" not in loaded.get("blocking_reasons", [])
    cred = next(r for r in loaded["checks"] if r["check"] == "railway_credential_readiness")
    assert cred["status"] == "pass"
    assert cred.get("canonical_token_present") is True


@patch("aethos_core.credentials.get_provider_api_token")
def test_follow_up_renderer_excludes_credential_blocker_from_stale_state(mock_token) -> None:
    mock_token.return_value = "railway-token-redacted"
    stale = {
        "simulation_id": "rsim-stale-render",
        "service_name": "aethos-api",
        "project": "pilotos",
        "environment": "production",
        "repo": "pilotmain/aethos",
        "branch": "main",
        "ready_to_execute": False,
        "blocking_reasons": ["railway_credential_not_ready", "env_values_not_configured"],
        "blocking_reason_messages": [
            "Railway credential or readonly inventory is not ready.",
            "Required env var values have not been supplied through a secure credential path.",
        ],
        "checks": [{"check": "railway_credential_readiness", "status": "fail"}],
    }
    body = render_blocking_followup(stale)
    assert "Railway credential or readonly inventory is not ready" not in body
    assert "env var values" in body.lower()


@patch("aethos_core.credentials.get_provider_api_token")
def test_normalized_simulation_persists_repaired_state(mock_token) -> None:
    mock_token.return_value = "railway-token-redacted"
    stale = {
        "simulation_id": "rsim-persist-98i",
        "blocking_reasons": ["railway_credential_not_ready"],
        "blocking_reason_messages": ["Railway credential or readonly inventory is not ready."],
        "checks": [{"check": "railway_credential_readiness", "status": "fail"}],
    }
    save_simulation(session_id="98i-persist", simulation=stale)
    get_simulation(session_id="98i-persist")
    stored = get_simulation(session_id="98i-persist")
    assert stored is not None
    assert "railway_credential_not_ready" not in stored.get("blocking_reasons", [])


@patch("aethos_core.credentials.get_provider_api_token")
def test_no_repair_when_token_truly_missing(mock_token) -> None:
    mock_token.return_value = None
    stale = {
        "simulation_id": "rsim-no-token",
        "blocking_reasons": ["railway_credential_not_ready", "env_values_not_configured"],
        "blocking_reason_messages": [
            "Railway credential or readonly inventory is not ready.",
            "Required env var values have not been supplied through a secure credential path.",
        ],
        "checks": [{"check": "railway_credential_readiness", "status": "fail", "canonical_token_present": False}],
    }
    normalized, repaired = normalize_simulation_snapshot(stale)
    assert repaired is False
    assert "railway_credential_not_ready" in normalized.get("blocking_reasons", [])


@patch("aethos_core.credentials.get_provider_api_token")
def test_blocking_route_sets_normalized_meta_when_stale_repaired(mock_token) -> None:
    mock_token.return_value = "railway-token-redacted"
    plan = _confirmed_plan()
    save_deployment_plan_context(session_id="98i-meta", plan=plan)
    save_creation_preflight(session_id="98i-meta", preflight=build_creation_preflight_from_plan(plan))
    save_simulation(
        session_id="98i-meta",
        simulation={
            "simulation_id": "rsim-meta",
            "repo": plan["repo"],
            "project": plan["project"],
            "environment": plan["environment"],
            "service_name": plan["service_name"],
            "branch": plan["branch"],
            "ready_to_execute": False,
            "blocking_reasons": ["railway_credential_not_ready", "env_values_not_configured"],
            "blocking_reason_messages": [
                "Railway credential or readonly inventory is not ready.",
                "Required env var values have not been supplied through a secure credential path.",
            ],
            "checks": [{"check": "railway_credential_readiness", "status": "fail"}],
        },
    )
    result = route_railway_service_creation_simulator(
        "what is blocking execution?",
        session_id="98i-meta",
    )
    assert result is not None
    _body, _intent, meta = result
    assert meta.get("normalized_stale_credential_blocker") == "true"
