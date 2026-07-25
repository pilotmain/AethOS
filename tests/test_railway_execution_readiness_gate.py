# SPDX-License-Identifier: Apache-2.0
"""FIX 101 — authoritative Railway execution readiness gate."""

from __future__ import annotations

from unittest.mock import patch

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
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests as clear_lifecycle,
)
from aethos_core.providers.railway.env_value_readiness.env_value_context import (
    clear_for_tests as clear_env,
)
from aethos_core.providers.railway.execution_contract.execution_contract_models import EXECUTION_ENABLED
from aethos_core.providers.railway.execution_contract.execution_context import (
    clear_for_tests as clear_execution_context,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
    get_or_create_execution_journal,
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
from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
    clear_for_tests as clear_simulation,
    save_simulation,
)


def setup_function() -> None:
    clear_plan()
    clear_preflight()
    clear_simulation()
    clear_lifecycle()
    clear_journal()
    clear_receipts()
    clear_execution_context()
    clear_env()


def _confirmed_plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-101",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["OPENAI_API_KEY"],
            "mutation_ready": True,
        }
    )


def _seed_lane(
    *,
    session_id: str,
    review_confirmed: bool = True,
    preflight_approved: bool = False,
    simulation_ready: bool = False,
) -> tuple[dict, dict, dict]:
    plan = _confirmed_plan()
    if not review_confirmed:
        plan = dict(plan)
        plan.pop("review_confirmed", None)
        plan.pop("review_confirmed_at", None)
    preflight = build_creation_preflight_from_plan(plan)
    preflight["preflight_approved"] = preflight_approved
    simulation = {
        "simulation_id": "rsim-101",
        "repo": plan["repo"],
        "ready_to_execute": simulation_ready,
        "blocking_reasons": [] if simulation_ready else ["env_values_not_configured"],
        "blocking_reason_messages": [],
        "checks": [],
    }
    save_deployment_plan_context(session_id=session_id, plan=plan)
    save_creation_preflight(session_id=session_id, preflight=preflight)
    save_simulation(session_id=session_id, simulation=simulation)
    return plan, preflight, simulation


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_missing_plan_blocks(mock_probe) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    gate = evaluate_railway_execution_readiness("101-no-plan")
    assert gate.ready is False
    assert gate.checks["deployment_plan"] == "fail"
    assert "plan_missing" in gate.blocking_reasons


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_unconfirmed_review_blocks(mock_probe) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    plan, preflight, simulation = _seed_lane(session_id="101-review", review_confirmed=False)
    gate = evaluate_railway_execution_readiness(
        "101-review",
        plan=plan,
        preflight=preflight,
        simulation=simulation,
    )
    assert gate.checks["review_confirmed"] == "fail"
    assert "review_not_confirmed" in gate.blocking_reasons


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_unapproved_preflight_blocks(mock_probe) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    plan, preflight, simulation = _seed_lane(session_id="101-pref", preflight_approved=False)
    gate = evaluate_railway_execution_readiness(
        "101-pref",
        plan=plan,
        preflight=preflight,
        simulation=simulation,
    )
    assert gate.checks["preflight_approved"] == "fail"
    assert "preflight_not_approved" in gate.blocking_reasons


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_env_readiness_missing_blocks(mock_probe) -> None:
    mock_probe.return_value = {"present": False, "secret": True, "source": "missing"}
    plan, preflight, simulation = _seed_lane(session_id="101-env", preflight_approved=True)
    gate = evaluate_railway_execution_readiness(
        "101-env",
        plan=plan,
        preflight=preflight,
        simulation=simulation,
    )
    assert gate.checks["env_readiness"] == "fail"
    assert gate.checks["critical_env_secrets_configured"] == "fail"
    assert "critical_env_values_missing" in gate.blocking_reasons


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_simulation_not_ready_blocks(mock_probe) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    plan, preflight, simulation = _seed_lane(
        session_id="101-sim",
        preflight_approved=True,
        simulation_ready=False,
    )
    gate = evaluate_railway_execution_readiness(
        "101-sim",
        plan=plan,
        preflight=preflight,
        simulation=simulation,
    )
    assert gate.checks["simulation_ready_to_execute"] == "fail"
    assert "simulation_not_ready" in gate.blocking_reasons


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_execution_enabled_false_blocks_ready(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    plan, preflight, simulation = _seed_lane(
        session_id="101-all-but-exec",
        preflight_approved=True,
        simulation_ready=True,
    )
    get_or_create_execution_journal(plan=plan, session_id="101-all-but-exec")
    gate = evaluate_railway_execution_readiness(
        "101-all-but-exec",
        plan=plan,
        preflight=preflight,
        simulation=simulation,
    )
    assert EXECUTION_ENABLED is False
    assert gate.checks["execution_enabled"] == "fail"
    assert gate.checks["execution_policy"] == "fail"
    assert gate.ready is False
    assert "execution_policy_disabled" in gate.blocking_reasons
    assert "Railway greenfield execution mode is disabled" in gate.contract_blockers


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_gate_output_used_by_execute_command(mock_probe) -> None:
    mock_probe.return_value = {"present": False, "secret": True, "source": "missing"}
    plan, preflight, simulation = _seed_lane(session_id="101-exec", preflight_approved=False)
    routed = route_railway_execution_contract(
        "execute railway service creation",
        session_id="101-exec",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_execution_contract_not_ready"
    assert meta["route_id"] == "railway_execution_contract"
    assert meta["mutation_performed"] == "false"
    assert meta["execution_gate_ready"] == "false"
    assert int(meta["blocking_count"]) >= 1
    assert "Gate checks:" in body
    assert "Preflight has not been approved." in body


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_readiness_gate_prompt_renders_matrix(mock_probe) -> None:
    mock_probe.return_value = {"present": False, "secret": True, "source": "missing"}
    _seed_lane(session_id="101-show", preflight_approved=False)
    routed = route_railway_execution_contract(
        "check railway execution readiness",
        session_id="101-show",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_execution_readiness_gate"
    assert meta["execution_gate_ready"] == "false"
    assert "# Railway Execution Readiness Gate" in body
    assert "ready_to_execute: **false**" in body
    assert "Gate checks:" in body
    assert "No Railway mutation has been performed." in body
