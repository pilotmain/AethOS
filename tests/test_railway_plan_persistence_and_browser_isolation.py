# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 95B — Railway plan persistence and browser route isolation."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.browser_observation.browser_observation_router import (
    is_browser_observation_capture_intent,
    is_browser_observation_lane_intent,
)
from aethos_core.chat.route_trace import clear_route_traces_for_tests
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    _CONTEXT_STORE,
    clear_for_tests,
    get_deployment_plan_context,
    resolve_deployment_plan_context,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_global_index import (
    load_latest_active_plan,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
    route_railway_new_service_plan,
)


def setup_function() -> None:
    clear_for_tests()
    clear_route_traces_for_tests()


def _sample_plan() -> dict:
    return {
        "repo": "pilotmain/aethos",
        "branch": "main",
        "project": "pilotos",
        "environment": "production",
        "service_name": "aethos-api",
        "runtime": "Python",
        "build_command": "pip install -r requirements.txt",
        "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
        "health_check_path": "/health",
        "stage": "plan_draft",
        "mutation_ready": False,
    }


def test_saved_plan_survives_session_cache_reset() -> None:
    save_deployment_plan_context(session_id="session-a", plan=_sample_plan())
    _CONTEXT_STORE.clear()
    assert get_deployment_plan_context(session_id="session-a") is not None
    assert load_latest_active_plan() is not None
    resolved = resolve_deployment_plan_context(session_id="session-b", user_text="")
    assert resolved is not None
    assert resolved.get("repo") == "pilotmain/aethos"


@patch("aethos_core.providers.railway.deployment_plan.plan_completion.inspect_github_repo_for_deployment")
def test_complete_plan_uses_latest_global_plan(mock_inspect) -> None:
    mock_inspect.return_value = {
        "ok": True,
        "repository": "pilotmain/aethos",
        "branch": "main",
        "fields": {
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/health",
            "required_env_var_names": [],
            "service_name_confidence": "low",
        },
    }
    save_deployment_plan_context(session_id="persist-orig", plan=_sample_plan())
    _CONTEXT_STORE.clear()

    result = route_railway_new_service_plan(
        "complete the railway deployment plan",
        session_id="new-session-empty",
    )
    assert result is not None
    body, intent, _meta = result
    assert "Railway Deployment Plan Completion" in body
    assert intent in {"railway_deployment_plan_complete", "railway_deployment_plan_completion"}
    assert "don't have a saved" not in body.lower()
    mock_inspect.assert_called_once()


def test_repo_inspection_prompt_not_routed_to_browser() -> None:
    prompt = "inspect repo and complete railway deployment plan for pilotmain/aethos"
    assert not is_browser_observation_capture_intent(prompt)
    assert not is_browser_observation_lane_intent(prompt)


@patch("aethos_core.browser_observation.browser_observation_router.route_browser_observation")
def test_browser_screenshot_still_works_for_domain(mock_route) -> None:
    mock_route.return_value = (
        "Captured screenshot of https://pilotmain.com",
        "browser_observation_captured",
        {"route_id": "browser_observation"},
    )
    assert is_browser_observation_capture_intent("take a screenshot of pilotmain.com")
    result = resolve_chat_turn(
        "take a screenshot of pilotmain.com",
        session_id="browser-iso",
        apply_relational_layer=False,
    )
    assert result.intent == "browser_observation_captured"
    mock_route.assert_called_once()


@patch("aethos_core.browser_observation.browser_observation_router.route_browser_observation")
@patch("aethos_core.providers.railway.deployment_plan.plan_completion.inspect_github_repo_for_deployment")
def test_complete_with_repo_runs_plan_lane_not_browser(mock_inspect, mock_browser) -> None:
    mock_inspect.return_value = {
        "ok": True,
        "repository": "pilotmain/aethos",
        "branch": "main",
        "fields": {
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/health",
            "required_env_var_names": [],
            "service_name_confidence": "low",
        },
    }
    result = resolve_chat_turn(
        "inspect repo and complete railway deployment plan for pilotmain/aethos",
        session_id="plan-not-browser",
        apply_relational_layer=False,
    )
    mock_browser.assert_not_called()
    assert "Railway Deployment Plan Completion" in result.reply
    assert result.intent in {"railway_deployment_plan_complete", "railway_deployment_plan_completion"}
