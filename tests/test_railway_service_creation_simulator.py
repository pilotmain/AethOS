# SPDX-License-Identifier: Apache-2.0
"""FIX 98 — Railway service creation execution readiness simulator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aethos_core.devops_intent_planner.devops_request_classifier import should_block_mutation_preflight
from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    clear_for_tests as clear_preflight,
    save_creation_preflight,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight import build_creation_preflight_from_plan
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests as clear_plan,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.service_creation_simulator.simulator_checks import (
    check_service_name_availability,
    run_all_simulator_checks,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
    clear_for_tests as clear_sim,
    get_simulation,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_result import (
    assess_simulator_preconditions,
    build_simulation_result,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)
from aethos_core.chat.service import resolve_chat_turn


def setup_function() -> None:
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
        clear_for_tests as clear_lifecycle,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
        clear_for_tests as clear_readiness,
    )

    clear_plan()
    clear_preflight()
    clear_sim()
    clear_lifecycle()
    clear_readiness()


def _confirmed_plan() -> dict:
    plan = {
        "plan_id": "plan-fix98",
        "repo": "pilotmain/aethos",
        "branch": "main",
        "project": "pilotos",
        "environment": "production",
        "service_name": "aethos-api",
        "runtime": "Python",
        "build_command": "pip install -r requirements.txt",
        "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
        "health_check_path": "/api/v1/health",
        "required_env_var_names": ["APP_ENV", "OPENAI_API_KEY"],
        "risk_tier": "T3_production_impacting",
        "mutation_ready": True,
        "stage": "plan_complete",
    }
    return apply_plan_review_confirmation(plan)


def _mock_inventory(*, existing_service: str | None = None) -> MagicMock:
    svc = MagicMock()
    svc.name = existing_service or "other-svc"
    env = MagicMock()
    env.name = "production"
    env.id = "env-1"
    env.services = [svc] if existing_service else []
    project = MagicMock()
    project.name = "pilotos"
    project.id = "proj-1"
    project.environments = [env]
    inventory = MagicMock()
    inventory.error = None
    inventory.projects = [project]
    return inventory


def _passing_checks() -> list[dict]:
    return [
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


def test_blocked_without_confirmed_plan() -> None:
    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="fix98-none",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_service_creation_simulation_not_ready"
    assert (
        "don't have a saved Railway deployment plan in this session" in body
        or "don't have a Railway deployment lifecycle" in body
    )


def test_blocked_without_preflight() -> None:
    save_deployment_plan_context(session_id="fix98-nopref", plan=_confirmed_plan())
    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="fix98-nopref",
    )
    assert result is not None
    _body, intent, _meta = result
    assert intent == "railway_service_creation_simulation_not_ready"


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_simulation_runs_after_plan_and_preflight(mock_checks, monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    mock_checks.return_value = _passing_checks()
    plan = _confirmed_plan()
    save_deployment_plan_context(session_id="fix98-run", plan=plan)
    save_creation_preflight(
        session_id="fix98-run",
        preflight=build_creation_preflight_from_plan(plan),
    )
    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="fix98-run",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_service_creation_simulation"
    assert meta["route_id"] == "railway_service_creation_simulator"
    assert meta["ready_to_execute"] == "false"
    assert meta["mutation_performed"] == "false"
    assert "Execution Simulation" in body
    assert "ready_to_execute: false" in body
    assert "greenfield" in body.lower() or "not wired" in body.lower()
    stored = get_simulation(session_id="fix98-run")
    assert stored is not None
    assert stored.get("ready_to_execute") is False


@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
def test_service_name_conflict_blocks(mock_discover) -> None:
    mock_discover.return_value = _mock_inventory(existing_service="aethos-api")
    pe = {"check": "railway_project_environment", "status": "pass"}
    row = check_service_name_availability(
        plan=_confirmed_plan(),
        project_environment_check=pe,
    )
    assert row["status"] == "fail"
    assert "already exists" in row["details"]
    assert "aethos-api-2" in (row.get("suggested_alternatives") or [])


def test_env_values_block_execution(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    simulation = build_simulation_result(
        plan=plan,
        preflight=preflight,
        checks=_passing_checks(),
    )
    assert simulation["ready_to_execute"] is False
    assert "env_values_not_configured" in simulation["blocking_reasons"]
    assert "greenfield_service_creation_not_wired" in simulation["blocking_reasons"]


def test_greenfield_api_surface_blocks(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    checks = run_all_simulator_checks(plan=plan, preflight=preflight)
    api = next(r for r in checks if r["check"] == "execution_api_surface")
    assert api["status"] == "blocked"
    simulation = build_simulation_result(plan=plan, preflight=preflight, checks=checks)
    assert "greenfield_service_creation_not_wired" in simulation["blocking_reasons"]


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_blocking_followup_uses_saved(mock_checks) -> None:
    mock_checks.return_value = _passing_checks()
    plan = _confirmed_plan()
    save_deployment_plan_context(session_id="fix98-follow", plan=plan)
    save_creation_preflight(session_id="fix98-follow", preflight=build_creation_preflight_from_plan(plan))
    route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="fix98-follow",
    )
    result = route_railway_service_creation_simulator(
        "what is blocking execution?",
        session_id="fix98-follow",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_service_creation_simulation_blocking"
    assert "Blocking reasons" in body
    assert "ready_to_execute: false" in body


@patch("aethos_core.chat.mutation_target_chat.gate_railway_mutation_preflight")
def test_restart_lane_unaffected(mock_gate) -> None:
    def _gate(text, params, operation_type):
        _ = text, operation_type
        return {**params, "target_resolved": True, "target_name": "pilotos-api"}, None

    mock_gate.side_effect = _gate
    binding = type("Binding", (), {"ok": True, "stored_github_repo": "", "referenced_github_repo": ""})()
    with patch(
        "aethos_core.provider_topology.binding_verifier.verify_source_binding",
        return_value=binding,
    ):
        result = resolve_chat_turn(
            "restart pilotos-api in railway",
            session_id="fix98-restart",
            apply_relational_layer=False,
        )
    assert result.intent != "railway_service_creation_simulation"
    assert "railway_service_creation_simulator" not in str(result.meta.get("route_id") or "")


def test_devops_preflight_blocked() -> None:
    assert should_block_mutation_preflight("simulate railway service creation") is True


def test_precondition_assessment() -> None:
    ok, blockers = assess_simulator_preconditions(plan=_confirmed_plan(), preflight=None)
    assert ok is False
    assert any("preflight" in b.lower() for b in blockers)
