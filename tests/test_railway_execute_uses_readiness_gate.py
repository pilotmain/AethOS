# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 101B — execute railway service creation must use execution readiness gate."""

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
from aethos_core.providers.railway.execution_contract.execution_context import (
    clear_for_tests as clear_execution_context,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
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
            "plan_id": "plan-101b",
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


def _assert_gate_style_response(body: str, intent: str, meta: dict) -> None:
    assert intent in {
        "railway_execution_contract_not_ready",
        "railway_execution_readiness_gate",
    }
    assert meta["route_id"] == "railway_execution_contract"
    assert meta["mutation_performed"] == "false"
    assert "# Railway Execution Readiness Gate" in body
    assert "Gate checks:" in body
    assert "Blocking reasons:" in body
    assert "fresh runtime state" not in body.lower()
    assert "no usable deployment plan could be materialized" not in body.lower()
    assert "Blocked until: preflight approval" not in body


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_execute_uses_gate_when_lifecycle_missing(mock_probe) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    routed = route_railway_execution_contract(
        "execute railway service creation",
        session_id="101b-fresh",
    )
    assert routed is not None
    body, intent, meta = routed
    _assert_gate_style_response(body, intent, meta)
    assert "- deployment plan: missing" in body
    assert "- review confirmed: no" in body
    assert "- preflight exists: no" in body
    assert "- simulation exists: no" in body
    assert "- execution enabled: no" in body


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_execute_uses_gate_when_preflight_missing(mock_probe) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    plan = _confirmed_plan()
    save_deployment_plan_context(session_id="101b-pref", plan=plan)
    routed = route_railway_execution_contract(
        "execute railway service creation",
        session_id="101b-pref",
    )
    assert routed is not None
    body, intent, meta = routed
    _assert_gate_style_response(body, intent, meta)
    assert "Preflight has not been approved." in body or "preflight has not been created" in body.lower()


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_execute_uses_gate_when_env_missing(mock_probe) -> None:
    mock_probe.return_value = {"present": False, "secret": True, "source": "missing"}
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    preflight["preflight_approved"] = True
    simulation = {
        "simulation_id": "rsim-101b",
        "repo": plan["repo"],
        "ready_to_execute": False,
        "blocking_reasons": ["env_values_not_configured"],
        "blocking_reason_messages": [],
        "checks": [],
    }
    save_deployment_plan_context(session_id="101b-env", plan=plan)
    save_creation_preflight(session_id="101b-env", preflight=preflight)
    save_simulation(session_id="101b-env", simulation=simulation)

    routed = route_railway_execution_contract(
        "execute railway service creation",
        session_id="101b-env",
    )
    assert routed is not None
    body, intent, meta = routed
    _assert_gate_style_response(body, intent, meta)
    assert "- env readiness: blocked" in body
    assert "Required critical env values are missing" in body
    assert "configure missing env values through Credential Center" in body


def test_execute_and_check_readiness_match_on_fresh_runtime() -> None:
    execute = route_railway_execution_contract(
        "execute railway service creation",
        session_id="101b-match",
    )
    check = route_railway_execution_contract(
        "check railway execution readiness",
        session_id="101b-match",
    )
    assert execute is not None and check is not None
    execute_body, execute_intent, _ = execute
    check_body, check_intent, _ = check
    assert execute_intent == "railway_execution_contract_not_ready"
    assert check_intent == "railway_execution_readiness_gate"
    assert "- deployment plan: missing" in execute_body
    assert "- deployment plan: missing" in check_body
    assert "fresh runtime state" not in execute_body.lower()
