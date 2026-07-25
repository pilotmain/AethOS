# SPDX-License-Identifier: Apache-2.0
"""FIX 104 — dry-run execution enrollment gate + receipt timeline."""

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
from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    EXECUTION_PHASES,
)
from aethos_core.providers.railway.execution_contract.execution_dry_run_executor import (
    run_dry_run_phase_execution,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
    get_or_create_execution_journal,
    load_journal_by_id,
)
from aethos_core.providers.railway.execution_contract.execution_readiness_gate import (
    evaluate_railway_execution_readiness,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    list_execution_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_router import (
    route_railway_execution_contract,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
    clear_for_tests as clear_simulation,
    get_simulation,
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


def _patch_disabled(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
    get_settings.cache_clear()


def _plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-104",
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
        "simulation_id": "rsim-104",
        "repo": plan["repo"],
        "ready_to_execute": True,
        "blocking_reasons": [],
        "blocking_reason_messages": [],
        "checks": [],
    }
    save_deployment_plan_context(session_id=session_id, plan=plan)
    save_creation_preflight(session_id=session_id, preflight=preflight)
    save_simulation(session_id=session_id, simulation=simulation)
    return plan


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_dry_run_gate_allows_phase_execution_not_real_mutation(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_dry_run(monkeypatch)
    plan = _seed_ready_lane("104-gate")
    gate = evaluate_railway_execution_readiness(
        "104-gate",
        plan=plan,
        preflight=get_creation_preflight(session_id="104-gate"),
        simulation=get_simulation(session_id="104-gate"),
    )
    assert gate.execution_mode == "dry_run"
    assert gate.phase_execution_allowed is True
    assert gate.real_mutation_allowed is False
    assert gate.checks["execution_enabled"] == "fail"
    assert gate.ready is True
    assert gate.can_enroll_execution() is True


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_disabled_mode_blocks_phase_execution(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_disabled(monkeypatch)
    plan = _seed_ready_lane("104-disabled")
    gate = evaluate_railway_execution_readiness(
        "104-disabled",
        plan=plan,
        preflight=get_creation_preflight(session_id="104-disabled"),
        simulation=get_simulation(session_id="104-disabled"),
    )
    assert gate.phase_execution_allowed is False
    assert gate.can_enroll_execution() is False


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_dry_run_execute_creates_receipts_and_phase_history(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_dry_run(monkeypatch)
    _seed_ready_lane("104-exec")
    routed = route_railway_execution_contract(
        "execute railway service creation",
        session_id="104-exec",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_execution_contract_requested"
    assert meta["phase_execution_allowed"] == "true"
    assert meta["real_mutation_allowed"] == "false"
    assert meta["mutation_performed"] == "false"
    assert int(meta["simulated_phase_count"]) == len(EXECUTION_PHASES)
    assert "simulated_success" in body or "Dry-run" in body

    routed2 = route_railway_execution_contract(
        "show railway execution timeline",
        session_id="104-exec",
    )
    assert routed2 is not None
    timeline_body, timeline_intent, _ = routed2
    assert timeline_intent == "railway_execution_timeline"
    assert "# Railway Execution Timeline" in timeline_body
    assert "create_service — simulated_success" in timeline_body
    assert "Mutation performed:" in timeline_body


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_rerun_skips_existing_phases_same_execution_id(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_dry_run(monkeypatch)
    _seed_ready_lane("104-rerun")
    first = route_railway_execution_contract(
        "execute railway service creation",
        session_id="104-rerun",
    )
    assert first is not None
    first_id = None
    routed_journal = route_railway_execution_contract(
        "show railway execution journal",
        session_id="104-rerun",
    )
    if routed_journal:
        body = routed_journal[0]
        for line in body.splitlines():
            if "execution_id:" in line:
                first_id = line.split("`")[1]
    second = route_railway_execution_contract(
        "execute railway service creation",
        session_id="104-rerun",
    )
    assert second is not None
    assert "Execution already simulated for:" in second[0]
    assert "No new simulated phases were executed." in second[0]
    if first_id:
        journal = load_journal_by_id(first_id)
        assert journal is not None
        assert journal["execution_id"] == first_id


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_simulated_failure_partial_failure_and_rollback_receipts(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_dry_run(monkeypatch)
    plan = _seed_ready_lane("104-fail")
    journal, _ = get_or_create_execution_journal(
        plan=plan,
        session_id="104-fail",
        initial_state="simulation_complete",
    )
    result = run_dry_run_phase_execution(
        journal=journal,
        plan=plan,
        failure_phase="trigger_deploy",
    )
    assert result.partial_failure is True
    assert result.journal["state"] == "execution_partial_failure"
    assert result.journal.get("rollback_available") is True
    receipts = list_execution_receipts(execution_id=str(journal["execution_id"]))
    phases = {r["phase"] for r in receipts}
    assert "trigger_deploy" in phases
    assert any(r.get("status") == "simulated_failure" for r in receipts)
    assert "rollback_create_service" in phases
    assert all(r.get("mutation_performed") is False for r in receipts)


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_receipts_render_enhanced_fields(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_dry_run(monkeypatch)
    _seed_ready_lane("104-receipts")
    route_railway_execution_contract(
        "execute railway service creation",
        session_id="104-receipts",
    )
    routed = route_railway_execution_contract(
        "show railway execution receipts",
        session_id="104-receipts",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_execution_contract_receipts"
    assert meta["mutation_performed"] == "false"
    assert "Receipt:" in body
    assert "replayed: **false**" in body
    assert "mutation_performed: **false**" in body
    assert "duration_ms:" in body
