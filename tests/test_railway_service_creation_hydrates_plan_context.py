# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 98B — preflight/simulator hydrate saved deployment plans from global index."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    clear_for_tests as clear_preflight,
    get_creation_preflight,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight_router import (
    route_railway_service_creation_preflight,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests as clear_lifecycle,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    _CONTEXT_STORE,
    clear_for_tests as clear_plan,
    get_deployment_plan_context,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_lifecycle import (
    resolve_and_materialize_deployment_plan,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
    route_railway_new_service_plan,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
    clear_for_tests as clear_sim,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)


def setup_function() -> None:
    clear_plan()
    clear_preflight()
    clear_lifecycle()
    clear_sim()


def _confirmed_plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-98b",
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
            "stage": "review_confirmed",
        }
    )


def test_preflight_uses_plan_from_global_index_after_session_reset() -> None:
    save_deployment_plan_context(session_id="session-orig-98b", plan=_confirmed_plan())
    _CONTEXT_STORE.clear()

    result = route_railway_service_creation_preflight(
        "create railway service creation preflight",
        session_id="session-new-98b",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_creation_preflight_draft"
    assert "don't have a saved Railway deployment plan" not in body
    assert "saved_deployment_plan" not in body.lower()
    assert get_deployment_plan_context(session_id="session-new-98b") is not None


def test_simulator_uses_confirmed_plan_from_global_index() -> None:
    save_deployment_plan_context(session_id="session-orig-sim", plan=_confirmed_plan())
    route_railway_service_creation_preflight(
        "create railway service creation preflight",
        session_id="session-orig-sim",
    )
    _CONTEXT_STORE.clear()

    with patch(
        "aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks"
    ) as mock_checks:
        mock_checks.return_value = [
            {"check": "railway_project_environment", "status": "pass"},
            {"check": "service_name_availability", "status": "pass"},
            {"check": "github_source_binding", "status": "pass"},
            {"check": "railway_credential_readiness", "status": "pass"},
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
        result = route_railway_service_creation_simulator(
            "simulate railway service creation",
            session_id="session-new-sim",
        )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_service_creation_simulation"
    assert "Cannot simulate Railway service creation yet" not in body
    assert "don't have a saved Railway deployment plan" not in body


def test_missing_state_distinguishes_no_plan() -> None:
    result = route_railway_service_creation_preflight(
        "create railway service creation preflight",
        session_id="empty-98b",
    )
    assert result is not None
    body, _intent, _meta = result
    assert "don't have a saved Railway deployment plan in this session" in body
    assert "create railway deployment plan for pilotmain/aethos" in body


def test_missing_state_distinguishes_unconfirmed_plan() -> None:
    plan = _confirmed_plan()
    plan.pop("review_confirmed", None)
    plan["stage"] = "plan_complete"
    save_deployment_plan_context(session_id="unconfirmed-98b", plan=plan)
    _CONTEXT_STORE.clear()

    result = route_railway_service_creation_preflight(
        "create railway service creation preflight",
        session_id="other-98b",
    )
    assert result is not None
    body, _intent, _meta = result
    assert "not confirmed yet" in body
    assert "confirm railway deployment plan" in body


def test_missing_state_distinguishes_missing_preflight_for_simulator() -> None:
    save_deployment_plan_context(session_id="confirmed-only", plan=_confirmed_plan())
    _CONTEXT_STORE.clear()

    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="sim-no-pref",
    )
    assert result is not None
    body, _intent, _meta = result
    assert "found the confirmed Railway deployment plan" in body
    assert "create railway service creation preflight" in body


def test_show_plan_and_simulator_resolver_agree() -> None:
    save_deployment_plan_context(session_id="agree-orig", plan=_confirmed_plan())
    _CONTEXT_STORE.clear()

    show = route_railway_new_service_plan(
        "show railway deployment plan",
        session_id="agree-new",
    )
    assert show is not None
    plan_from_show = resolve_and_materialize_deployment_plan(
        session_id="agree-new",
        user_text="show railway deployment plan",
    )
    plan_from_sim = resolve_and_materialize_deployment_plan(
        session_id="agree-new",
        user_text="simulate railway service creation",
    )
    assert plan_from_show is not None
    assert plan_from_sim is not None
    assert plan_from_show.get("plan_id") == plan_from_sim.get("plan_id")
    assert plan_from_show.get("repo") == plan_from_sim.get("repo")
    _body, intent, _meta = show
    assert intent == "railway_deployment_plan_show"
