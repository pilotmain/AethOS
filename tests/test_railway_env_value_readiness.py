# SPDX-License-Identifier: Apache-2.0
"""FIX 99 — Railway secure env value readiness."""

from __future__ import annotations

import os
from unittest.mock import patch

from aethos_core.config import get_settings
from aethos_core.chat.service import resolve_chat_turn
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
from aethos_core.providers.railway.env_value_readiness.env_value_context import (
    clear_for_tests as clear_env_ctx,
    get_env_value_readiness,
)
from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
    clear_deployment_env_presence_for_tests,
    set_deployment_env_presence_for_tests,
)
from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
    assess_env_value_readiness,
    build_target_key,
    is_secret_env_name,
)
from aethos_core.providers.railway.env_value_readiness.env_value_router import (
    route_railway_env_value_readiness,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_checks import (
    check_required_env_var_readiness,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_result import (
    build_simulation_result,
)


def setup_function() -> None:
    import os

    from aethos_core.config import get_settings

    os.environ["RAILWAY_GREENFIELD_EXECUTION_MODE"] = "disabled"
    get_settings.cache_clear()
    clear_plan()
    clear_preflight()
    clear_env_ctx()
    clear_deployment_env_presence_for_tests()


def _plan(*, env_names: list[str] | None = None) -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-99",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": env_names or ["APP_ENV", "API_PORT", "OPENAI_API_KEY"],
            "mutation_ready": True,
        }
    )


def test_non_secret_defaults_marked_present() -> None:
    state = assess_env_value_readiness(plan=_plan(env_names=["APP_ENV", "API_PORT"]))
    assert state["values"]["APP_ENV"]["present"] is True
    assert state["values"]["APP_ENV"]["secret"] is False
    assert state["values"]["API_PORT"]["source"] == "deployment_default"


@patch("aethos_core.credentials.get_provider_api_token", return_value=None)
def test_secret_missing_when_not_in_secure_store(mock_token) -> None:
    with patch.dict(os.environ, {"RAILWAY_GREENFIELD_EXECUTION_MODE": "disabled"}, clear=True):
        get_settings.cache_clear()
        state = assess_env_value_readiness(plan=_plan())
    assert "OPENAI_API_KEY" in state["missing"]
    assert state["ready"] is False


@patch("aethos_core.credentials.get_provider_api_token")
def test_secret_present_from_credential_center(mock_token) -> None:
    mock_token.return_value = "sk-test-redacted"
    state = assess_env_value_readiness(plan=_plan())
    assert state["values"]["OPENAI_API_KEY"]["present"] is True
    assert state["values"]["OPENAI_API_KEY"]["source"] == "credential_center"
    assert state["ready"] is True


def test_secret_values_never_in_report() -> None:
    with patch.dict(os.environ, {"OPENAI_API_KEY": "super-secret-value"}, clear=False):
        result = route_railway_env_value_readiness(
            "check railway env value readiness",
            session_id="sec-99",
        )
    assert result is not None
    body, _intent, _meta = result
    assert "super-secret-value" not in body
    assert "sk-" not in body.lower() or "OPENAI_API_KEY" in body


@patch("aethos_core.security.credential_vault.get_credential_vault")
@patch("aethos_core.credentials.get_provider_api_token", return_value=None)
def test_mark_configured_does_not_blindly_pass(mock_token, mock_vault) -> None:
    mock_vault.return_value.list_credentials.return_value = []
    mock_vault.return_value.retrieve_secret.return_value = {}
    with patch.dict(os.environ, {"RAILWAY_GREENFIELD_EXECUTION_MODE": "disabled"}, clear=True):
        get_settings.cache_clear()
        save_deployment_plan_context(
            session_id="mark-99",
            plan=_plan(env_names=["OPENAI_API_KEY"]),
        )
        mark = route_railway_env_value_readiness(
            "mark railway env values configured",
            session_id="mark-99",
        )
        refresh = route_railway_env_value_readiness(
            "refresh railway env readiness",
            session_id="mark-99",
        )
    assert mark is not None
    assert "verify secure presence" in mark[0].lower()
    assert refresh is not None
    assert refresh[2].get("env_value_ready") == "false"


@patch("aethos_core.credentials.get_provider_api_token")
def test_refresh_passes_when_secure_store_reports_presence(mock_token) -> None:
    mock_token.return_value = "token"
    save_deployment_plan_context(session_id="refresh-99", plan=_plan())
    result = route_railway_env_value_readiness(
        "refresh railway env readiness",
        session_id="refresh-99",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_env_value_readiness_refresh"
    assert meta.get("env_value_ready") == "true"
    assert "ready: true" in body.lower() or "ready: **true**" in body


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_simulator_env_pass_when_readiness_ready(mock_checks) -> None:
    plan = _plan(env_names=["APP_ENV", "API_PORT"])
    preflight = build_creation_preflight_from_plan(plan)
    mock_checks.return_value = [
        {"check": "railway_credential_readiness", "status": "pass", "canonical_token_present": True},
        {
            "check": "required_env_var_readiness",
            "status": "pass",
            "env_var_values_status": "pass",
            "env_value_ready": True,
        },
        {"check": "execution_api_surface", "status": "blocked"},
    ]
    simulation = build_simulation_result(plan=plan, preflight=preflight, checks=mock_checks.return_value)
    assert "env_values_not_configured" not in simulation["blocking_reasons"]
    assert "greenfield_service_creation_not_wired" in simulation["blocking_reasons"]


def test_simulator_integration_env_ready_only_greenfield_blocked() -> None:
    plan = _plan(env_names=["APP_ENV", "API_PORT"])
    preflight = build_creation_preflight_from_plan(plan)
    row = check_required_env_var_readiness(plan=plan, session_id="sim-int-99")
    assert row["env_var_values_status"] in {"pass", "pass_with_defaults"}
    simulation = build_simulation_result(plan=plan, preflight=preflight, session_id="sim-int-99")
    assert "env_values_not_configured" not in simulation["blocking_reasons"]


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_plan_and_preflight_include_env_readiness_metadata(mock_checks) -> None:
    mock_checks.return_value = [{"check": "execution_api_surface", "status": "blocked"}]
    plan = _plan()
    session = "meta-99"
    save_deployment_plan_context(session_id=session, plan=plan)
    save_creation_preflight(session_id=session, preflight=build_creation_preflight_from_plan(plan))
    from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
        route_railway_new_service_plan,
    )

    show = route_railway_new_service_plan("show railway deployment plan", session_id=session)
    assert show is not None
    assert "Env value readiness:" in show[0]

    from aethos_core.providers.railway.deployment_plan.creation_preflight_router import (
        route_railway_service_creation_preflight,
    )

    pre = route_railway_service_creation_preflight(
        "create railway service creation preflight",
        session_id=session,
    )
    assert pre is not None
    assert "Env value readiness:" in pre[0]


def test_restart_lane_unaffected() -> None:
    from aethos_core.providers.railway.env_value_readiness.env_value_intent import (
        is_railway_env_value_intent,
    )

    assert is_railway_env_value_intent("restart pilotos-api in railway") is False


def test_browser_lane_unaffected() -> None:
    from aethos_core.browser_observation.browser_observation_router import (
        is_browser_observation_lane_intent,
    )
    from aethos_core.providers.railway.env_value_readiness.env_value_intent import (
        is_railway_env_value_intent,
    )

    assert is_browser_observation_lane_intent("take screenshot of the app") is True
    assert is_railway_env_value_intent("take screenshot of the app") is False


def test_github_workflow_lane_unaffected() -> None:
    from aethos_core.providers.railway.env_value_readiness.env_value_intent import (
        is_railway_env_value_intent,
    )

    assert is_railway_env_value_intent("create github workflow for ci") is False


def test_env_readiness_route_ownership() -> None:
    save_deployment_plan_context(session_id="route-99", plan=_plan(env_names=["APP_ENV"]))
    result = route_railway_env_value_readiness(
        "check railway env value readiness",
        session_id="route-99",
    )
    assert result is not None
    _body, intent, meta = result
    assert intent == "railway_env_value_readiness_check"
    assert meta.get("route_id") == "railway_env_value_readiness"
    assert meta.get("mutation_performed") == "false"


def test_persisted_state_has_no_secret_values() -> None:
    from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
        get_or_assess_env_value_readiness,
    )

    with patch.dict(os.environ, {"OPENAI_API_KEY": "hidden"}, clear=False):
        get_or_assess_env_value_readiness(plan=_plan(), session_id="persist-99")
    stored = get_env_value_readiness(session_id="persist-99", plan=_plan())
    assert stored is not None
    blob = str(stored)
    assert "hidden" not in blob


def test_is_secret_classification() -> None:
    assert is_secret_env_name("OPENAI_API_KEY") is True
    assert is_secret_env_name("APP_ENV") is False


def test_deployment_env_presence_store() -> None:
    plan = _plan()
    key = build_target_key(
        repo=plan["repo"],
        project=plan["project"],
        environment=plan["environment"],
        service_name=plan["service_name"],
    )
    set_deployment_env_presence_for_tests(target_key=key, present_names=["OPENAI_API_KEY"])
    with patch.dict(os.environ, {}, clear=True):
        state = assess_env_value_readiness(plan=plan)
    assert state["ready"] is True
