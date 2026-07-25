# SPDX-License-Identifier: Apache-2.0
"""FIX 93 — Railway deployment plan reply completeness."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests,
    get_deployment_plan_context,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_intent import (
    is_railway_new_service_plan_intent,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
    route_railway_new_service_plan,
)

_REQUIRED_SECTIONS = (
    "# Railway New Service Deployment Plan",
    "Target source:",
    "Railway target:",
    "Build/runtime:",
    "Required env vars:",
    "Governed execution plan:",
    "Risk:",
    "Rollback:",
    "Verification:",
    "No service has been created.",
    "No mutation has been performed.",
)


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


def _assert_full_plan(body: str) -> None:
    for section in _REQUIRED_SECTIONS:
        assert section in body, f"missing section: {section}"
    assert "1. Create Railway service" in body
    assert "T3 production impacting" in body or "T2 staging/dev" in body


@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_create_plan_with_target_returns_full_plan(mock_checks, mock_options) -> None:
    mock_checks.return_value = _passed_readiness_checks()
    mock_options.return_value = []
    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="plan-93-create",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_plan_draft"
    _assert_full_plan(body)
    assert "pilotmain/aethos" in body
    assert "pilotos" in body
    assert "production" in body
    assert "aethos-api" in body
    assert "Readiness: all readonly checks passed" in body
    assert "Railway deployment readiness checks passed" not in body
    assert "one readonly check failed" not in body.lower()


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_show_plan_returns_full_plan(mock_checks) -> None:
    mock_checks.return_value = _passed_readiness_checks()
    save_deployment_plan_context(
        session_id="plan-93-show",
        plan={
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
            "stage": "plan_draft",
            "mutation_ready": False,
        },
    )
    result = route_railway_new_service_plan(
        "show railway deployment plan",
        session_id="plan-93-show",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_plan_show"
    _assert_full_plan(body)
    assert "pilotmain/aethos" in body
    assert "aethos-api" in body
    mock_checks.assert_not_called()


@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_readiness_text_does_not_replace_plan(mock_checks, mock_options) -> None:
    mock_checks.return_value = _passed_readiness_checks()
    mock_options.return_value = []
    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="plan-93-readiness",
    )
    assert result is not None
    body, _, _ = result
    plan_pos = body.index("# Railway New Service Deployment Plan")
    readiness_pos = body.index("Readiness:")
    assert readiness_pos < plan_pos
    assert body[plan_pos:].startswith("# Railway New Service Deployment Plan")
    assert "Governed execution plan:" in body[plan_pos:]


@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_no_mutation_performed(mock_checks, mock_options) -> None:
    mock_checks.return_value = _passed_readiness_checks()
    mock_options.return_value = []
    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="plan-93-mutation",
    )
    assert result is not None
    _body, _intent, meta = result
    assert meta.get("mutation_performed") == "false"
    stored = get_deployment_plan_context(session_id="plan-93-mutation")
    assert stored is not None
    assert stored.get("mutation_ready") is False


def test_restart_lane_unaffected() -> None:
    assert not is_railway_new_service_plan_intent("restart pilotos-api in railway")
