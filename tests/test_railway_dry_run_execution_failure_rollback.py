# SPDX-License-Identifier: Apache-2.0
"""FIX 106 — dry-run failure, partial_failure, rollback timeline/receipts, safe rerun."""

from __future__ import annotations

from unittest.mock import patch

import pytest

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
from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    EXECUTION_PHASES,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    clear_for_tests as clear_execution_context,
)
from aethos_core.providers.railway.execution_contract.execution_dry_run_executor import (
    parse_simulated_failure_phase,
    run_dry_run_phase_execution,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
    get_or_create_execution_journal,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    list_execution_receipts,
    list_forward_phase_receipts,
    list_rollback_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_router import (
    assess_execution_approvals,
    request_execution_contract,
    route_railway_execution_contract,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
    clear_for_tests as clear_simulation,
    save_simulation,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)


def setup_function() -> None:
    clear_plan()
    clear_preflight()
    clear_simulation()
    clear_lifecycle()
    clear_journal()
    clear_receipts()
    clear_execution_context()
    get_settings.cache_clear()


def _patch_dry_run(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "dry_run")
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS", "staging,development,production")
    get_settings.cache_clear()


def _plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-106",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "staging",
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["APP_ENV"],
            "mutation_ready": True,
        }
    )


def _seed_ready_lane(session_id: str) -> tuple[dict, dict, dict]:
    plan = _plan()
    preflight = build_creation_preflight_from_plan(plan)
    preflight["preflight_approved"] = True
    simulation = {
        "simulation_id": "rsim-106",
        "repo": plan["repo"],
        "ready_to_execute": True,
        "blocking_reasons": [],
        "blocking_reason_messages": [],
        "checks": [],
    }
    save_deployment_plan_context(session_id=session_id, plan=plan)
    save_creation_preflight(session_id=session_id, preflight=preflight)
    save_simulation(session_id=session_id, simulation=simulation)
    return plan, preflight, simulation


def _phase_index(phase: str) -> int:
    return list(EXECUTION_PHASES).index(phase)  # type: ignore[arg-type]


@pytest.mark.parametrize("failure_phase", EXECUTION_PHASES)
def test_simulated_failure_at_each_phase_stops_remaining(monkeypatch, failure_phase: str) -> None:
    _patch_dry_run(monkeypatch)
    plan = _plan()
    journal, _ = get_or_create_execution_journal(
        plan=plan,
        session_id=f"106-{failure_phase}",
        initial_state="simulation_complete",
    )
    result = run_dry_run_phase_execution(
        journal=journal,
        plan=plan,
        failure_phase=failure_phase,
    )
    assert result.partial_failure is True
    assert result.failure_phase == failure_phase
    assert result.journal["state"] == "execution_partial_failure"
    assert result.journal.get("rollback_available") is True

    execution_id = str(journal["execution_id"])
    forward = list_forward_phase_receipts(execution_id=execution_id)
    forward_phases = [str(r["phase"]) for r in forward]
    fail_idx = _phase_index(failure_phase)
    assert failure_phase in forward_phases
    for phase in EXECUTION_PHASES[fail_idx + 1 :]:
        assert phase not in forward_phases

    rollback = list_rollback_receipts(execution_id=execution_id)
    assert len(rollback) == fail_idx
    if fail_idx > 0:
        assert rollback
    assert all(r.get("mutation_performed") is False for r in list_execution_receipts(execution_id=execution_id))


def test_parse_failure_from_execute_prompt() -> None:
    assert parse_simulated_failure_phase(
        "execute railway service creation with trigger_deploy failure"
    ) == "trigger_deploy"
    assert parse_simulated_failure_phase(
        "simulate railway service creation with create_service failure"
    ) == "create_service"


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_execute_with_failure_shows_rollback_views(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_dry_run(monkeypatch)
    session = "106-rollback-views"
    plan, preflight, simulation = _seed_ready_lane(session)
    approval = assess_execution_approvals(plan=plan, preflight=preflight, simulation=simulation)
    approval["user_text"] = "execute railway service creation with configure_env failure"
    approval["simulated_failure_phase"] = "configure_env"

    first = request_execution_contract(plan=plan, session_id=session, approval=approval)
    assert first["ok"] is True
    assert first["journal"]["state"] == "execution_partial_failure"

    timeline = route_railway_execution_contract(
        "show railway rollback timeline",
        session_id=session,
    )
    assert timeline is not None
    body, intent, meta = timeline
    assert intent == "railway_execution_rollback_timeline"
    assert meta["mutation_performed"] == "false"
    assert "rollback_create_service" in body
    assert "failure_phase: `configure_env`" in body

    receipts_view = route_railway_execution_contract(
        "show railway rollback receipts",
        session_id=session,
    )
    assert receipts_view is not None
    r_body, r_intent, r_meta = receipts_view
    assert r_intent == "railway_execution_rollback_receipts"
    assert r_meta["mutation_performed"] == "false"
    assert "rollback_configure_env" not in r_body
    assert "rollback_create_service" in r_body
    assert "mutation_performed: **false**" in r_body

    exec_timeline = route_railway_execution_contract(
        "show railway execution timeline",
        session_id=session,
    )
    assert exec_timeline is not None
    assert "Partial failure:" in exec_timeline[0]
    assert "configure_env" in exec_timeline[0]


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_rerun_after_partial_failure_is_idempotent(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_dry_run(monkeypatch)
    session = "106-rerun-partial"
    plan, preflight, simulation = _seed_ready_lane(session)
    approval = assess_execution_approvals(plan=plan, preflight=preflight, simulation=simulation)
    approval["simulated_failure_phase"] = "trigger_deploy"
    approval["user_text"] = "execute railway service creation with trigger_deploy failure"

    first = request_execution_contract(plan=plan, session_id=session, approval=approval)
    execution_id = str(first["journal"]["execution_id"])
    count_after_first = len(list_execution_receipts(execution_id=execution_id))
    rollback_after_first = len(list_rollback_receipts(execution_id=execution_id))

    second = request_execution_contract(plan=plan, session_id=session, approval=approval)
    assert second["ok"] is True
    assert second["journal"]["execution_id"] == execution_id
    assert len(list_execution_receipts(execution_id=execution_id)) == count_after_first
    assert len(list_rollback_receipts(execution_id=execution_id)) == rollback_after_first

    routed = route_railway_execution_contract(
        "execute railway service creation",
        session_id=session,
    )
    assert routed is not None
    assert "partial_failure" in routed[0].lower() or "already" in routed[0].lower()


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_simulator_delegates_failure_simulation_to_execution_contract(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_dry_run(monkeypatch)
    session = "106-sim-delegate"
    _seed_ready_lane(session)
    routed = route_railway_service_creation_simulator(
        "simulate railway service creation with verify_runtime failure",
        session_id=session,
    )
    assert routed is not None
    assert routed[2]["route_id"] == "railway_execution_contract"
    assert routed[1] == "railway_execution_contract_requested"
    execution_id = str(routed[2].get("execution_id") or "")
    if execution_id:
        journal_receipts = list_execution_receipts(execution_id=execution_id)
        assert any(r.get("status") == "simulated_failure" for r in journal_receipts)
