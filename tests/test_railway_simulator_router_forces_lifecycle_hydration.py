# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 98K — simulator router forces lifecycle ensure before missing-artifact exits."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests as clear_lifecycle,
    save_lifecycle_record,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight import build_creation_preflight_from_plan
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    _CONTEXT_STORE,
    clear_for_tests as clear_plan,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.service_creation_simulator.simulator_context import clear_for_tests as clear_sim
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)


def setup_function() -> None:
    clear_plan()
    clear_sim()
    clear_lifecycle()


def _confirmed_plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-98k",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["APP_ENV"],
            "mutation_ready": True,
        }
    )


def _lifecycle_record(*, session_id: str, include_simulation: bool = False) -> dict:
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    record = {
        "lifecycle_id": "rlc-98k",
        "session_id": session_id,
        "repo": plan["repo"],
        "branch": plan["branch"],
        "project": plan["project"],
        "environment": plan["environment"],
        "service_name": plan["service_name"],
        "readiness": {"status": "passed", "checked_at": "2026-05-26T00:00:00Z", "checks": {}},
        "plan": {
            "exists": True,
            "mutation_ready": True,
            "review_confirmed": True,
            "snapshot": dict(plan),
        },
        "preflight": {
            "exists": True,
            "preflight_id": preflight["preflight_id"],
            "approved": False,
            "snapshot": dict(preflight),
        },
        "simulation": {"exists": False, "ready_to_execute": False, "blocking_reasons": [], "snapshot": {}},
    }
    if include_simulation:
        record["simulation"] = {
            "exists": True,
            "ready_to_execute": False,
            "blocking_reasons": ["env_values_not_configured"],
            "snapshot": {
                "simulation_id": "rsim-98k",
                "repo": plan["repo"],
                "project": plan["project"],
                "environment": plan["environment"],
                "service_name": plan["service_name"],
                "branch": plan["branch"],
                "ready_to_execute": False,
                "blocking_reasons": ["env_values_not_configured"],
                "checks": [{"check": "railway_credential_readiness", "status": "pass"}],
            },
        }
    return record


@patch(
    "aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration.ensure_railway_deployment_lifecycle_for_lane"
)
@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_simulator_router_calls_lifecycle_ensure_before_missing_plan(mock_checks, mock_ensure) -> None:
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        LifecycleLaneState,
    )

    mock_checks.return_value = [{"check": "execution_api_surface", "status": "blocked"}]
    mock_ensure.return_value = LifecycleLaneState(
        lifecycle=None,
        plan=None,
        preflight=None,
        simulation=None,
        hydrated_from_global=False,
        hydration_notice=None,
        ensure_called=True,
        ensure_result="miss",
    )
    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="98k-miss",
    )
    assert result is not None
    assert mock_ensure.called
    body, intent, meta = result
    assert intent == "railway_service_creation_simulation_not_ready"
    assert "fresh runtime state" in body.lower()
    assert meta.get("lifecycle_ensure_called") == "true"
    assert meta.get("lifecycle_ensure_result") == "miss"


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_global_lifecycle_with_plan_materializes_and_simulator_runs(mock_checks) -> None:
    mock_checks.return_value = [
        {"check": "railway_credential_readiness", "status": "pass", "canonical_token_present": True},
        {"check": "required_env_var_readiness", "status": "blocked", "env_var_values_status": "blocked"},
        {"check": "execution_api_surface", "status": "blocked"},
    ]
    save_lifecycle_record(session_id="98k-orig", record=_lifecycle_record(session_id="98k-orig"))
    _CONTEXT_STORE.clear()

    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="98k-new",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_service_creation_simulation"
    assert "don't have a saved Railway deployment plan" not in body
    assert meta.get("lifecycle_ensure_called") == "true"
    assert meta.get("lifecycle_ensure_result") in {"hit", "partial"}


@patch("aethos_core.credentials.get_provider_api_token")
def test_global_lifecycle_with_simulation_materializes_followup(mock_token) -> None:
    mock_token.return_value = "railway-token"
    save_lifecycle_record(
        session_id="98k-follow-orig",
        record=_lifecycle_record(session_id="98k-follow-orig", include_simulation=True),
    )
    _CONTEXT_STORE.clear()
    clear_sim()

    result = route_railway_service_creation_simulator(
        "what failed in the dry run?",
        session_id="98k-follow-new",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_service_creation_simulation_failed"
    assert intent != "railway_service_creation_simulation_failed_missing"
    assert "No saved simulation" not in body
    assert meta.get("lifecycle_ensure_called") == "true"
    assert meta.get("hydrated_from_global_lifecycle") == "true"


def test_missing_lifecycle_returns_diagnostic_no_plan_reply() -> None:
    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="98k-empty",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_service_creation_simulation_not_ready"
    assert "fresh runtime state" in body.lower()
    assert "global lifecycle index: **missing**" in body
    assert meta.get("lifecycle_ensure_called") == "true"
    assert meta.get("lifecycle_ensure_result") == "miss"
