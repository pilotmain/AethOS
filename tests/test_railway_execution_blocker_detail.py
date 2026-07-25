# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 100B — detailed Railway execution request blocker replies."""

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
from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    EXECUTION_ENABLED,
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
            "plan_id": "plan-100b",
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


def _seed_partial_lane(*, session_id: str, preflight_approved: bool = False) -> None:
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    preflight["preflight_approved"] = preflight_approved
    simulation = {
        "simulation_id": "rsim-100b",
        "repo": plan["repo"],
        "branch": plan["branch"],
        "project": plan["project"],
        "environment": plan["environment"],
        "service_name": plan["service_name"],
        "ready_to_execute": False,
        "blocking_reasons": ["env_values_not_configured"],
        "blocking_reason_messages": [
            "Required env var values have not been supplied through a secure credential path."
        ],
        "checks": [],
    }
    save_deployment_plan_context(session_id=session_id, plan=plan)
    save_creation_preflight(session_id=session_id, preflight=preflight)
    save_simulation(session_id=session_id, simulation=simulation)


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_execution_blocker_reply_includes_gate_matrix(mock_probe) -> None:
    mock_probe.return_value = {"present": False, "secret": True, "source": "missing"}
    _seed_partial_lane(session_id="100b-block", preflight_approved=False)

    routed = route_railway_execution_contract(
        "execute railway service creation",
        session_id="100b-block",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_execution_contract_not_ready"
    assert meta["mutation_performed"] == "false"
    assert "Gate checks:" in body
    assert "- deployment plan: ready" in body
    assert "- review confirmed: yes" in body
    assert "- preflight exists: yes" in body
    assert "- preflight approved: no" in body
    assert "- simulation exists: yes" in body
    assert "- simulation ready: no" in body
    assert "- env readiness: blocked" in body
    assert f"- execution enabled: {'true' if EXECUTION_ENABLED else 'no'}" in body
    assert "Blocked until: preflight approval" not in body


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_preflight_and_env_blockers_listed_separately(mock_probe) -> None:
    mock_probe.return_value = {"present": False, "secret": True, "source": "missing"}
    _seed_partial_lane(session_id="100b-sep", preflight_approved=False)

    body, _, _ = route_railway_execution_contract(
        "execute railway service creation",
        session_id="100b-sep",
    )
    assert "Preflight has not been approved." in body
    assert "Required critical env values are missing" in body
    assert "Simulation is not ready to execute" in body
    assert "approve railway service creation preflight" in body
    assert "configure missing env values through Credential Center" in body


def test_execution_enabled_false_shown_without_execute_implication() -> None:
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    preflight["preflight_approved"] = True
    simulation = {
        "simulation_id": "rsim-ok",
        "repo": plan["repo"],
        "ready_to_execute": True,
        "blocking_reasons": [],
        "checks": [],
    }
    save_deployment_plan_context(session_id="100b-exec-off", plan=plan)
    save_creation_preflight(session_id="100b-exec-off", preflight=preflight)
    save_simulation(session_id="100b-exec-off", simulation=simulation)

    with patch(
        "aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence",
        return_value={"present": True, "secret": False, "source": "configured"},
    ):
        body, intent, _ = route_railway_execution_contract(
            "execute railway service creation",
            session_id="100b-exec-off",
        )

    assert EXECUTION_ENABLED is False
    if intent == "railway_execution_contract_requested":
        assert "execution enabled: false" in body.lower() or "execution_enabled: **false**" in body
    assert "No Railway mutation has been performed." in body
