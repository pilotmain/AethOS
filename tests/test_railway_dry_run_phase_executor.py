# SPDX-License-Identifier: Apache-2.0
"""FIX 103 — dry-run phase executor."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.creation_preflight import (
    build_creation_preflight_from_plan,
)
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
from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    EXECUTION_PHASES,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
    get_or_create_execution_journal,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    list_execution_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_dry_run_executor import (
    run_dry_run_phase_execution,
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
    get_settings.cache_clear()


def _patch_dry_run(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "dry_run")
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS", "staging,development,production")
    get_settings.cache_clear()


def _plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-103",
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


def _seed_ready_lane(session_id: str) -> dict:
    plan = _plan()
    preflight = build_creation_preflight_from_plan(plan)
    preflight["preflight_approved"] = True
    simulation = {
        "simulation_id": "rsim-103",
        "repo": plan["repo"],
        "ready_to_execute": True,
        "blocking_reasons": [],
        "blocking_reason_messages": [],
        "checks": [],
    }
    save_deployment_plan_context(session_id=session_id, plan=plan)
    save_creation_preflight(session_id=session_id, preflight=preflight)
    save_simulation(session_id=session_id, simulation=simulation)
    journal, _ = get_or_create_execution_journal(
        plan=plan,
        session_id=session_id,
        initial_state="simulation_complete",
        approval={"simulation_complete": True},
    )
    return journal


def test_dry_run_executor_records_phases_without_mutation() -> None:
    journal = _seed_ready_lane("103-unit")
    result = run_dry_run_phase_execution(journal=journal, plan=_plan())
    journal = result.journal
    assert journal["state"] == "execution_completed"
    receipts = list_execution_receipts(execution_id=str(journal["execution_id"]))
    assert len(receipts) == len(EXECUTION_PHASES)
    assert all(r.get("mutation_performed") is False for r in receipts)
    assert all(r.get("status") == "simulated_success" for r in receipts)


def test_dry_run_executor_is_idempotent() -> None:
    journal = _seed_ready_lane("103-idem")
    first = run_dry_run_phase_execution(journal=journal, plan=_plan())
    second = run_dry_run_phase_execution(journal=first.journal, plan=_plan())
    assert second.journal["state"] == "execution_completed"
    receipts = list_execution_receipts(execution_id=str(journal["execution_id"]))
    assert len(receipts) == len(EXECUTION_PHASES)


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_execute_in_dry_run_mode_runs_phase_executor(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_dry_run(monkeypatch)
    _seed_ready_lane("103-exec")
    routed = route_railway_execution_contract(
        "execute railway service creation",
        session_id="103-exec",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_execution_contract_requested"
    assert meta["mutation_performed"] == "false"
    assert "Dry-run phases simulated step-by-step" in body
