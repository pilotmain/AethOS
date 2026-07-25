# SPDX-License-Identifier: Apache-2.0
"""FIX 97 — Railway new-service creation preflight (no execution)."""

from __future__ import annotations

from aethos_core.devops_intent_planner.devops_request_classifier import should_block_mutation_preflight
from aethos_core.providers.railway.deployment_plan.creation_preflight import (
    compose_creation_preflight_artifact,
    plan_eligible_for_creation_preflight,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    clear_for_tests as clear_preflight,
    get_creation_preflight,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight_router import (
    route_railway_service_creation_preflight,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests as clear_plan,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation


def setup_function() -> None:
    clear_plan()
    clear_preflight()


def _confirmed_plan() -> dict:
    plan = {
        "plan_id": "plan-fix97",
        "repo": "pilotmain/aethos",
        "branch": "main",
        "project": "pilotos",
        "environment": "production",
        "service_name": "aethos-api",
        "runtime": "Python",
        "build_command": "pip install -r requirements.txt",
        "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
        "health_check_path": "/api/v1/health",
        "required_env_var_names": ["APP_ENV", "OPENAI_API_KEY", "API_PORT"],
        "env_var_summary": {
            "groups": {
                "Core runtime": ["APP_ENV", "API_PORT"],
                "AI providers": ["OPENAI_API_KEY"],
            },
            "additional_count": 0,
            "total_count": 3,
        },
        "risk_tier": "T3_production_impacting",
        "mutation_ready": True,
        "stage": "plan_complete",
    }
    return apply_plan_review_confirmation(plan)


def test_preflight_requires_confirmed_plan() -> None:
    save_deployment_plan_context(session_id="fix97", plan=_confirmed_plan())
    result = route_railway_service_creation_preflight(
        "create railway service creation preflight",
        session_id="fix97",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_creation_preflight_draft"
    assert meta.get("route_id") == "railway_deployment_creation_preflight"
    assert meta.get("mutation_performed") == "false"
    assert meta.get("execution_enabled") == "false"
    assert "Blast radius" in body
    assert "Service creation diff" in body
    assert "Rollback" in body
    assert "still unset" in body.lower()
    assert "APP_ENV" in body
    assert "service_creation_execution: **not enabled yet**" in body
    assert "preflight_approved: false" in body
    stored = get_creation_preflight(session_id="fix97")
    assert stored is not None
    assert stored.get("preflight_approved") is False


def test_preflight_blocked_without_review_confirmed() -> None:
    plan = _confirmed_plan()
    plan.pop("review_confirmed", None)
    plan.pop("stage", None)
    save_deployment_plan_context(session_id="fix97-blocked", plan=plan)
    result = route_railway_service_creation_preflight(
        "create railway service creation preflight",
        session_id="fix97-blocked",
    )
    assert result is not None
    _body, intent, _meta = result
    assert intent == "railway_creation_preflight_not_ready"


def test_approve_preflight_still_no_execution() -> None:
    save_deployment_plan_context(session_id="fix97-approve", plan=_confirmed_plan())
    route_railway_service_creation_preflight(
        "create railway service creation preflight",
        session_id="fix97-approve",
    )
    result = route_railway_service_creation_preflight(
        "approve railway service creation preflight",
        session_id="fix97-approve",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_creation_preflight_approved"
    assert meta.get("preflight_approved") == "true"
    assert meta.get("mutation_performed") == "false"
    assert "preflight_approved: true" in body
    assert "No Railway service has been created" in body
    assert "not enabled yet" in body
    stored = get_creation_preflight(session_id="fix97-approve")
    assert stored is not None
    assert stored.get("preflight_approved") is True


def test_compose_artifact_sections() -> None:
    plan = _confirmed_plan()
    from aethos_core.providers.railway.deployment_plan.creation_preflight import (
        build_creation_preflight_from_plan,
    )

    preflight = build_creation_preflight_from_plan(plan)
    body = compose_creation_preflight_artifact(preflight)
    assert "+ service: aethos-api  (new)" in body
    assert "T3 production impacting" in body
    assert "OPENAI_API_KEY" in body


def test_eligible_gate() -> None:
    ok, blockers = plan_eligible_for_creation_preflight(_confirmed_plan())
    assert ok is True
    assert blockers == []
    partial = {"repo": "pilotmain/aethos", "start_command": "unknown"}
    ok2, blockers2 = plan_eligible_for_creation_preflight(partial)
    assert ok2 is False
    assert "review_confirmed" in blockers2


def test_devops_mutation_preflight_blocked() -> None:
    assert should_block_mutation_preflight("create railway service creation preflight") is True
