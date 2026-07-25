# SPDX-License-Identifier: Apache-2.0
"""FIX 99B — Railway env criticality and deployment profiles."""

from __future__ import annotations

import os
from unittest.mock import patch

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
from aethos_core.providers.railway.env_value_readiness.env_classification import (
    DeploymentProfile,
    EnvCriticality,
    classify_env_var,
    default_runtime_value,
    should_block_deployment,
)
from aethos_core.providers.railway.env_value_readiness.env_value_context import clear_for_tests as clear_env_ctx
from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
    clear_deployment_env_presence_for_tests,
)
from aethos_core.providers.railway.env_value_readiness.env_value_readiness import assess_env_value_readiness
from aethos_core.providers.railway.env_value_readiness.env_value_router import route_railway_env_value_readiness
from aethos_core.providers.railway.service_creation_simulator.simulator_checks import (
    check_required_env_var_readiness,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_result import build_simulation_result


def setup_function() -> None:
    clear_plan()
    clear_preflight()
    clear_env_ctx()
    clear_deployment_env_presence_for_tests()


def _plan(*, env_names: list[str] | None = None) -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-99b",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": env_names
            or [
                "APP_ENV",
                "API_PORT",
                "ANTHROPIC_API_KEY",
                "WEB_SEARCH_API_KEY",
                "BROWSER_HEADLESS",
                "TELEGRAM_TYPING_INTERVAL_SECONDS",
                "LOCAL_WORKSPACE_ARTIFACTS_DIR",
            ],
            "mutation_ready": True,
        }
    )


def test_classify_criticality_buckets() -> None:
    profile = DeploymentProfile.RAILWAY_PRODUCTION.value
    assert classify_env_var("ANTHROPIC_API_KEY", profile=profile) == EnvCriticality.CRITICAL_SECRET
    assert classify_env_var("APP_ENV", profile=profile) == EnvCriticality.CRITICAL_RUNTIME
    assert classify_env_var("BROWSER_HEADLESS", profile=profile) == EnvCriticality.DEFAULTABLE_RUNTIME
    assert classify_env_var("TELEGRAM_TYPING_INTERVAL_SECONDS", profile=profile) == EnvCriticality.OPTIONAL_FEATURE
    assert classify_env_var("LOCAL_WORKSPACE_ARTIFACTS_DIR", profile=profile) == EnvCriticality.DEVELOPMENT_ONLY


def test_critical_secrets_block_deployment() -> None:
    with patch.dict(os.environ, {}, clear=True):
        state = assess_env_value_readiness(plan=_plan(env_names=["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"]))
    assert state["ready"] is False
    assert "ANTHROPIC_API_KEY" in state["critical_missing"]


@patch("aethos_core.credentials.get_provider_api_token")
def test_optional_and_defaultable_do_not_block(mock_token) -> None:
    mock_token.return_value = "token-present"
    with patch.dict(os.environ, {}, clear=True):
        state = assess_env_value_readiness(plan=_plan())
    assert state["ready"] is True
    assert state["ready_mode"] == "pass_with_defaults"
    assert "TELEGRAM_TYPING_INTERVAL_SECONDS" in state["optional_missing"]
    assert "LOCAL_WORKSPACE_ARTIFACTS_DIR" in state["ignored_dev_only"]
    assert any(row["name"] == "BROWSER_HEADLESS" for row in state["using_defaults"])


def test_development_only_ignored_for_railway_production() -> None:
    state = assess_env_value_readiness(
        plan=_plan(env_names=["LOCAL_WORKSPACE_ARTIFACTS_DIR", "RESEARCH_ARTIFACTS_DIR", "APP_ENV", "API_PORT"])
    )
    assert "LOCAL_WORKSPACE_ARTIFACTS_DIR" in state["ignored_dev_only"]
    assert state["ready"] is True


def test_defaultable_runtime_uses_profile_defaults() -> None:
    value = default_runtime_value("BROWSER_HEADLESS", profile=DeploymentProfile.RAILWAY_PRODUCTION.value)
    assert value is not None
    assert value[0] == "true"


def test_simulator_pass_with_defaults_when_only_optional_missing(mock_token=None) -> None:
    with patch("aethos_core.credentials.get_provider_api_token", return_value="tok"):
        plan = _plan()
        preflight = build_creation_preflight_from_plan(plan)
        row = check_required_env_var_readiness(plan=plan, session_id="99b-sim")
        simulation = build_simulation_result(plan=plan, preflight=preflight, session_id="99b-sim")
    assert row["env_var_values_status"] == "pass_with_defaults"
    assert "env_values_not_configured" not in simulation["blocking_reasons"]
    assert "greenfield_service_creation_not_wired" in simulation["blocking_reasons"]


def test_simulator_only_greenfield_when_secrets_satisfied() -> None:
    with patch("aethos_core.credentials.get_provider_api_token", return_value="tok"):
        plan = _plan(
            env_names=[
                "APP_ENV",
                "API_PORT",
                "ANTHROPIC_API_KEY",
                "WEB_SEARCH_API_KEY",
                "TELEGRAM_TYPING_INTERVAL_SECONDS",
            ]
        )
        preflight = build_creation_preflight_from_plan(plan)
        simulation = build_simulation_result(plan=plan, preflight=preflight, session_id="99b-green")
    assert "env_values_not_configured" not in simulation["blocking_reasons"]
    assert "greenfield_service_creation_not_wired" in simulation["blocking_reasons"]


def test_report_sections_and_no_secrets_printed() -> None:
    save_deployment_plan_context(session_id="99b-report", plan=_plan())
    with patch("aethos_core.credentials.get_provider_api_token", return_value="super-secret-token"):
        result = route_railway_env_value_readiness(
            "check railway env value readiness",
            session_id="99b-report",
        )
    assert result is not None
    body, _intent, meta = result
    assert "super-secret-token" not in body
    assert "Using deployment defaults:" in body or "using deployment defaults:" in body.lower()
    assert meta.get("env_profile") == "railway_production"
    assert int(meta.get("optional_missing_count") or 0) >= 0


def test_plan_artifact_includes_classification_sections() -> None:
    session = "99b-plan"
    plan = _plan()
    save_deployment_plan_context(session_id=session, plan=plan)
    from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
        route_railway_new_service_plan,
    )

    with patch("aethos_core.credentials.get_provider_api_token", return_value="tok"):
        show = route_railway_new_service_plan("show railway deployment plan", session_id=session)
    assert show is not None
    body = show[0]
    assert "Env value readiness:" in body
    assert "mode:" in body


def test_should_block_only_critical() -> None:
    profile = DeploymentProfile.RAILWAY_PRODUCTION.value
    assert should_block_deployment("ANTHROPIC_API_KEY", profile=profile, present=False) is True
    assert should_block_deployment("TELEGRAM_TYPING_INTERVAL_SECONDS", profile=profile, present=False) is False
    assert should_block_deployment("LOCAL_WORKSPACE_ARTIFACTS_DIR", profile=profile, present=False) is False


def test_restart_lane_unaffected() -> None:
    from aethos_core.providers.railway.env_value_readiness.env_value_intent import is_railway_env_value_intent

    assert is_railway_env_value_intent("restart pilotos-api in railway") is False


def test_browser_lane_unaffected() -> None:
    from aethos_core.providers.railway.env_value_readiness.env_value_intent import is_railway_env_value_intent

    assert is_railway_env_value_intent("take screenshot of the app") is False


def test_github_workflow_lane_unaffected() -> None:
    from aethos_core.providers.railway.env_value_readiness.env_value_intent import is_railway_env_value_intent

    assert is_railway_env_value_intent("create github workflow for ci") is False


@patch("aethos_core.credentials.get_provider_api_token")
def test_chat_simulate_reflects_pass_with_defaults(mock_token) -> None:
    mock_token.return_value = "tok"
    session = "99b-chat"
    plan = _plan()
    save_deployment_plan_context(session_id=session, plan=plan)
    save_creation_preflight(session_id=session, preflight=build_creation_preflight_from_plan(plan))
    sim = resolve_chat_turn(
        "simulate railway service creation",
        session_id=session,
        apply_relational_layer=False,
    )
    assert sim.meta.get("route_id") == "railway_service_creation_simulator"
    assert "env_values_not_configured" not in (sim.meta.get("blocking_reasons") or "")
    assert "pass_with_defaults" in sim.reply or "greenfield" in sim.reply.lower()
