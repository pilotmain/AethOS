# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 104B — dry-run simulation readiness decoupled from mutation wiring."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.creation_preflight import (
    build_creation_preflight_from_plan,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    clear_for_tests as clear_preflight,
    get_creation_preflight,
    save_creation_preflight,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests as clear_plan,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests as clear_lifecycle,
)
from aethos_core.providers.railway.env_value_readiness.env_value_context import (
    clear_for_tests as clear_env,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    clear_for_tests as clear_execution_context,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
)
from aethos_core.providers.railway.execution_contract.execution_readiness_gate import (
    evaluate_railway_execution_readiness,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_router import (
    route_railway_execution_contract,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_checks import (
    check_execution_api_surface,
    run_all_simulator_checks,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
    clear_for_tests as clear_simulation,
    get_simulation,
    save_simulation,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_result import (
    build_simulation_result,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)
def _fully_passing_checks() -> list[dict]:
    return [
        {"check": "railway_project_environment", "status": "pass"},
        {"check": "service_name_availability", "status": "pass"},
        {"check": "github_source_binding", "status": "pass"},
        {"check": "railway_credential_readiness", "status": "pass"},
        {
            "check": "required_env_var_readiness",
            "status": "pass",
            "env_var_names_status": "pass",
            "env_var_values_status": "pass",
        },
        {"check": "build_start_health_readiness", "status": "pass"},
        {"check": "rollback_readiness", "status": "pass"},
        {"check": "execution_api_surface", "status": "blocked"},
    ]


def setup_function() -> None:
    clear_plan()
    clear_preflight()
    clear_simulation()
    clear_lifecycle()
    clear_journal()
    clear_receipts()
    clear_execution_context()
    clear_env()
    get_settings.cache_clear()


def _patch_dry_run(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "dry_run")
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS", "staging,development,production")
    get_settings.cache_clear()


def _patch_disabled(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
    get_settings.cache_clear()


def _plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-104b",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "staging",
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["OPENAI_API_KEY"],
            "mutation_ready": True,
        }
    )


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_dry_run_simulation_ready_without_mutation_wiring(mock_checks, monkeypatch) -> None:
    _patch_dry_run(monkeypatch)
    checks = _fully_passing_checks()
    mock_checks.return_value = checks
    plan = _plan()
    preflight = build_creation_preflight_from_plan(plan)
    simulation = build_simulation_result(plan=plan, preflight=preflight, checks=checks)
    assert simulation["ready_to_execute"] is True
    assert "greenfield_service_creation_not_wired" not in simulation["blocking_reasons"]
    api = next(r for r in simulation["checks"] if r["check"] == "execution_api_surface")
    assert api["status"] == "pass"


def test_disabled_mode_still_blocks_on_not_wired(monkeypatch) -> None:
    _patch_disabled(monkeypatch)
    plan = _plan()
    preflight = build_creation_preflight_from_plan(plan)
    checks = run_all_simulator_checks(plan=plan, preflight=preflight)
    simulation = build_simulation_result(plan=plan, preflight=preflight, checks=checks)
    assert simulation["ready_to_execute"] is False
    assert "greenfield_service_creation_not_wired" in simulation["blocking_reasons"]


def test_dry_run_api_surface_check_passes(monkeypatch) -> None:
    _patch_dry_run(monkeypatch)
    row = check_execution_api_surface()
    assert row["status"] == "pass"
    assert row.get("dry_run_exempt") is True


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
@patch(
    "aethos_core.providers.railway.service_creation_simulator.simulator_result.run_all_simulator_checks"
)
def test_simulate_then_execute_end_to_end(mock_checks, mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_dry_run(monkeypatch)
    mock_checks.return_value = _fully_passing_checks()
    plan = _plan()
    save_deployment_plan_context(session_id="104b-e2e", plan=plan)
    preflight = build_creation_preflight_from_plan(plan)
    preflight["preflight_approved"] = True
    save_creation_preflight(session_id="104b-e2e", preflight=preflight)
    sim_route = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="104b-e2e",
    )
    assert sim_route is not None
    assert sim_route[2]["ready_to_execute"] == "true"
    stored = get_simulation(session_id="104b-e2e")
    assert stored is not None
    assert stored["ready_to_execute"] is True

    gate = evaluate_railway_execution_readiness(
        "104b-e2e",
        plan=plan,
        preflight=get_creation_preflight(session_id="104b-e2e"),
        simulation=stored,
    )
    assert gate.phase_execution_allowed is True
    assert gate.can_enroll_execution() is True

    exec_route = route_railway_execution_contract(
        "execute railway service creation",
        session_id="104b-e2e",
    )
    assert exec_route is not None
    assert exec_route[1] == "railway_execution_contract_requested"
    assert exec_route[2]["mutation_performed"] == "false"
    assert int(exec_route[2]["simulated_phase_count"]) >= 5

    timeline = route_railway_execution_contract(
        "show railway execution timeline",
        session_id="104b-e2e",
    )
    assert timeline is not None
    assert "create_service — simulated_success" in timeline[0]
