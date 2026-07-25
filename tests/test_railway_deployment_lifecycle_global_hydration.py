# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 98D — canonical Railway deployment lifecycle global hydration."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
    lifecycle_plan_snapshot,
    lifecycle_preflight_snapshot,
    lifecycle_readiness_passed,
    lifecycle_simulation_snapshot,
    resolve_railway_deployment_lifecycle,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests as clear_lifecycle,
    get_lifecycle_session,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight import build_creation_preflight_from_plan
from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    clear_for_tests as clear_preflight,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight_router import (
    route_railway_service_creation_preflight,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    _CONTEXT_STORE,
    clear_for_tests as clear_plan,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
    route_railway_new_service_plan,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
    clear_for_tests as clear_readiness,
    save_readiness_context,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
    clear_for_tests as clear_sim,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)


def setup_function() -> None:
    clear_plan()
    clear_preflight()
    clear_sim()
    clear_readiness()
    clear_lifecycle()


def _passed_readiness_checks() -> dict:
    return {
        "readonly_readiness_ok": True,
        "mutation_ready": False,
        "railway_credential_ok": True,
        "referenced_github_repo": "pilotmain/aethos",
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": True, "project_count": 1, "environment_count": 1, "service_count": 1, "projects": []},
        "github_binding": {"github_credential_ok": True},
        "service_creation": {"graphql_service_create": False},
    }


def _confirmed_plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-98d",
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


def test_full_lifecycle_record_materializes() -> None:
    save_readiness_context(session_id="lc-orig", checks=_passed_readiness_checks())
    plan = _confirmed_plan()
    save_deployment_plan_context(session_id="lc-orig", plan=plan)
    preflight = build_creation_preflight_from_plan(plan)
    from aethos_core.providers.railway.deployment_plan.creation_preflight_context import save_creation_preflight

    save_creation_preflight(session_id="lc-orig", preflight=preflight)

    lifecycle = resolve_railway_deployment_lifecycle(session_id="lc-new", user_text="")
    assert lifecycle is not None
    assert lifecycle_readiness_passed(lifecycle)
    assert lifecycle_plan_snapshot(lifecycle) is not None
    assert lifecycle_preflight_snapshot(lifecycle) is not None
    stored = get_lifecycle_session(session_id="lc-new")
    assert stored is not None
    assert stored.get("plan", {}).get("review_confirmed") is True


def test_show_plan_after_session_reset() -> None:
    save_deployment_plan_context(session_id="show-orig", plan=_confirmed_plan())
    _CONTEXT_STORE.clear()

    result = route_railway_new_service_plan(
        "show railway deployment plan",
        session_id="show-new",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_plan_show"
    assert "don't have a saved" not in body.lower()


def test_preflight_after_session_reset() -> None:
    save_deployment_plan_context(session_id="pref-orig", plan=_confirmed_plan())
    _CONTEXT_STORE.clear()

    result = route_railway_service_creation_preflight(
        "create railway service creation preflight",
        session_id="pref-new",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_creation_preflight_draft"
    assert "don't have a saved Railway deployment plan" not in body


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_simulate_after_session_reset(mock_checks) -> None:
    mock_checks.return_value = [
        {"check": "railway_credential_readiness", "status": "pass"},
        {"check": "required_env_var_readiness", "status": "blocked", "env_var_values_status": "blocked"},
        {"check": "execution_api_surface", "status": "blocked"},
    ]
    plan = _confirmed_plan()
    save_deployment_plan_context(session_id="sim-orig", plan=plan)
    from aethos_core.providers.railway.deployment_plan.creation_preflight_context import save_creation_preflight

    save_creation_preflight(session_id="sim-orig", preflight=build_creation_preflight_from_plan(plan))
    _CONTEXT_STORE.clear()

    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="sim-new",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_service_creation_simulation"
    assert "Cannot simulate Railway service creation yet" not in body


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
def test_create_plan_uses_stored_readiness(mock_options, mock_readiness) -> None:
    mock_options.return_value = []
    mock_readiness.side_effect = AssertionError("should not rerun readiness when lifecycle has passed")
    save_readiness_context(session_id="plan-readiness", checks=_passed_readiness_checks())
    resolve_railway_deployment_lifecycle(session_id="plan-readiness", user_text="")

    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="plan-readiness",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_plan_draft"
    assert "readiness must pass" not in body.lower()


def test_legacy_stores_materialize_into_lifecycle() -> None:
    clear_lifecycle()
    save_deployment_plan_context(session_id="legacy-only", plan=_confirmed_plan())
    lifecycle = resolve_railway_deployment_lifecycle(session_id="other", user_text="")
    assert lifecycle is not None
    assert lifecycle_plan_snapshot(lifecycle) is not None
