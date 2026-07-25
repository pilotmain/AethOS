# SPDX-License-Identifier: Apache-2.0
"""FIX 96 — Railway deployment plan review and confirmation."""

from __future__ import annotations

from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests,
    get_deployment_plan_context,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
    route_railway_new_service_plan,
)
from aethos_core.providers.railway.deployment_plan.plan_review import (
    apply_plan_review_confirmation,
    compose_plan_review_request,
    is_plan_review_confirmed,
)


def setup_function() -> None:
    clear_for_tests()


def _complete_plan() -> dict:
    return {
        "repo": "pilotmain/aethos",
        "branch": "main",
        "project": "pilotos",
        "environment": "production",
        "service_name": "aethos-api",
        "runtime": "Python",
        "build_command": "pip install -r requirements.txt",
        "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
        "health_check_path": "/api/v1/health",
        "required_env_var_names": ["APP_ENV", "API_PORT"],
        "env_var_summary": {
            "groups": {"Core runtime": ["APP_ENV", "API_PORT"]},
            "additional_count": 0,
            "total_count": 2,
        },
        "risk_tier": "T3_production_impacting",
        "deployment_readiness": "complete",
        "mutation_ready": True,
        "stage": "plan_complete",
    }


def test_review_shows_assumptions() -> None:
    plan = _complete_plan()
    body = compose_plan_review_request(plan)
    assert "aethos-api" in body
    assert "pilotos" in body
    assert "production" in body
    assert "uvicorn" in body
    assert "T3 production impacting" in body
    assert "APP_ENV" in body
    assert "confirm railway deployment plan" in body


def test_confirm_sets_review_confirmed() -> None:
    save_deployment_plan_context(session_id="fix-96", plan=_complete_plan())
    result = route_railway_new_service_plan(
        "confirm railway deployment plan",
        session_id="fix-96",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_deployment_plan_confirm"
    assert "review_confirmed: true" in body
    assert meta.get("review_confirmed") == "true"
    assert meta.get("mutation_performed") == "false"
    stored = get_deployment_plan_context(session_id="fix-96")
    assert stored is not None
    assert is_plan_review_confirmed(stored)
    assert stored.get("stage") == "review_confirmed"


def test_confirm_already_confirmed() -> None:
    plan = apply_plan_review_confirmation(_complete_plan())
    save_deployment_plan_context(session_id="fix-96-already", plan=plan)
    result = route_railway_new_service_plan(
        "confirm railway deployment plan",
        session_id="fix-96-already",
    )
    assert result is not None
    _body, intent, _meta = result
    assert intent == "railway_deployment_plan_confirm_already"


def test_review_route_requires_saved_plan() -> None:
    result = route_railway_new_service_plan(
        "review railway deployment plan",
        session_id="empty-96",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_plan_review_not_ready"
    assert "don't have a saved" in body.lower()


def test_confirm_not_ready_when_plan_incomplete() -> None:
    save_deployment_plan_context(
        session_id="fix-96-partial",
        plan={
            "repo": "pilotmain/aethos",
            "project": "pilotos",
            "environment": "production",
            "start_command": "unknown",
        },
    )
    result = route_railway_new_service_plan(
        "confirm railway deployment plan",
        session_id="fix-96-partial",
    )
    assert result is not None
    _body, intent, _meta = result
    assert intent == "railway_deployment_plan_confirm_not_ready"
