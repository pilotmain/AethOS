# SPDX-License-Identifier: Apache-2.0
"""FIX 92 — Railway new-service deployment plan artifact."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests,
    get_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_intent import (
    is_railway_new_service_plan_intent,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
    route_railway_new_service_plan,
)
from aethos_core.chat.service import resolve_chat_turn


def setup_function() -> None:
    clear_for_tests()


def _passed_readiness_checks() -> dict:
    return {
        "readonly_readiness_ok": True,
        "mutation_ready": False,
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": True, "project_count": 1, "environment_count": 1, "service_count": 1, "projects": []},
        "github_binding": {"github_credential_ok": True},
        "service_creation": {},
    }


@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_creates_plan_after_readiness(mock_checks, mock_options) -> None:
    mock_checks.return_value = _passed_readiness_checks()
    mock_options.return_value = []
    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="plan-92",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_deployment_plan_draft"
    assert meta["route_id"] == "railway_deployment_plan"
    assert "# Railway New Service Deployment Plan" in body
    assert "pilotmain/aethos" in body
    assert "pilotos" in body
    assert "production" in body
    assert "Governed execution plan:" in body
    assert "Verification:" in body
    assert "Readiness: all readonly checks passed" in body
    assert "Railway deployment readiness checks passed" not in body
    assert "No service has been created." in body
    assert "No mutation has been performed." in body
    stored = get_deployment_plan_context(session_id="plan-92")
    assert stored is not None
    assert stored["repo"] == "pilotmain/aethos"
    assert stored["stage"] == "plan_draft"
    assert stored["mutation_ready"] is False


@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_asks_targeted_project_environment_clarification(mock_checks, mock_options) -> None:
    mock_checks.return_value = _passed_readiness_checks()
    mock_options.return_value = [
        {"project": "pilotos", "environment": "production", "path": "pilotos / production"},
        {"project": "atlas-trader", "environment": "production", "path": "atlas-trader / production"},
    ]
    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos",
        session_id="plan-clarify",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_deployment_plan_clarification"
    assert "Which Railway project/environment" in body
    assert "pilotos / production" in body
    assert "atlas-trader / production" in body
    assert "one readonly check failed" not in body.lower()


def test_not_workflow_lane_intent() -> None:
    from aethos_core.providers.github.workflow_lane.workflow_lane_guards import has_github_workflow_lane_intent

    assert is_railway_new_service_plan_intent("create railway deployment plan for pilotmain/aethos")
    assert not has_github_workflow_lane_intent("create railway deployment plan for pilotmain/aethos")


def test_not_existing_restart_lane() -> None:
    assert not is_railway_new_service_plan_intent("restart pilotos-api in railway")
    assert is_railway_new_service_plan_intent("prepare new Railway service plan")


@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_router.route_railway_new_service_plan")
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_resolve_chat_turn_routes_plan_lane(mock_checks, mock_plan) -> None:
    mock_checks.return_value = _passed_readiness_checks()
    mock_plan.return_value = (
        "# Railway New Service Deployment Plan\n\nNo mutation has been performed.",
        "railway_deployment_plan_draft",
        {"route_id": "railway_deployment_plan"},
    )
    result = resolve_chat_turn(
        "create railway deployment plan for pilotmain/aethos",
        session_id="chat-plan",
        apply_relational_layer=False,
    )
    assert result.intent == "railway_deployment_plan_draft"
    assert "How I can help" not in result.reply
    mock_plan.assert_called_once()
