# SPDX-License-Identifier: Apache-2.0
"""FIX 100 — Railway greenfield service creation execution contract."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from aethos_core.config import get_settings

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
from aethos_core.providers.railway.execution_contract.execution_context import (
    acquire_execution_lock,
    clear_for_tests as clear_execution_context,
    load_execution_lock,
)
from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    EXECUTION_ENABLED,
    EXECUTION_PHASES,
)
from aethos_core.providers.railway.execution_contract.execution_idempotency import (
    derive_idempotency_key,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
    get_or_create_execution_journal,
    load_journal_by_idempotency_key,
    new_execution_journal,
    save_execution_journal,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    list_execution_receipts,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import (
    attach_rollback_journal,
    build_rollback_journal,
)
from aethos_core.providers.railway.execution_contract.execution_router import (
    assess_execution_approvals,
    request_execution_contract,
    route_railway_execution_contract,
)
from aethos_core.providers.railway.execution_contract.execution_state_machine import (
    IllegalExecutionTransitionError,
    assert_transition,
    can_transition,
    transition_journal_state,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests as clear_lifecycle,
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


def _confirmed_plan(*, environment: str = "staging") -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-100",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": environment,
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["APP_ENV"],
            "mutation_ready": True,
        }
    )


def _seed_ready_lane(*, session_id: str) -> tuple[dict, dict, dict]:
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    preflight["preflight_approved"] = True
    simulation = {
        "simulation_id": "rsim-100",
        "repo": plan["repo"],
        "branch": plan["branch"],
        "project": plan["project"],
        "environment": plan["environment"],
        "service_name": plan["service_name"],
        "ready_to_execute": True,
        "blocking_reasons": [],
        "checks": [],
    }
    save_deployment_plan_context(session_id=session_id, plan=plan)
    save_creation_preflight(session_id=session_id, preflight=preflight)
    save_simulation(session_id=session_id, simulation=simulation)
    return plan, preflight, simulation


def test_valid_execution_state_transitions() -> None:
    journal = new_execution_journal(plan=_confirmed_plan(), session_id="st-1", initial_state="draft")
    journal = transition_journal_state(journal, to_state="review_confirmed")
    journal = transition_journal_state(journal, to_state="preflight_created")
    journal = transition_journal_state(journal, to_state="preflight_approved")
    journal = transition_journal_state(journal, to_state="simulation_complete")
    journal = transition_journal_state(journal, to_state="execution_requested")
    journal = transition_journal_state(journal, to_state="execution_locked")
    assert journal["state"] == "execution_locked"
    assert can_transition(from_state="execution_locked", to_state="execution_phase_create_service")


def test_illegal_transitions_rejected() -> None:
    assert not can_transition(from_state="draft", to_state="execution_locked")
    with pytest.raises(IllegalExecutionTransitionError):
        assert_transition(from_state="draft", to_state="execution_locked")
    with pytest.raises(IllegalExecutionTransitionError):
        transition_journal_state({"state": "draft"}, to_state="execution_completed")


def test_idempotency_key_stable() -> None:
    plan = _confirmed_plan()
    key_a = derive_idempotency_key(plan=plan)
    key_b = derive_idempotency_key(plan=dict(plan))
    assert key_a == key_b
    assert key_a.startswith("ridem-")


def test_repeated_execution_request_reuses_same_journal() -> None:
    plan, preflight, simulation = _seed_ready_lane(session_id="idem-1")
    approval = assess_execution_approvals(plan=plan, preflight=preflight, simulation=simulation)

    first = request_execution_contract(plan=plan, session_id="idem-1", approval=approval)
    second = request_execution_contract(plan=plan, session_id="idem-1", approval=approval)

    assert first["ok"] is True
    assert second["ok"] is True
    assert first["journal"]["execution_id"] == second["journal"]["execution_id"]
    assert second["journal_created"] is False
    loaded = load_journal_by_idempotency_key(first["journal"]["idempotency_key"])
    assert loaded is not None
    assert loaded["execution_id"] == first["journal"]["execution_id"]


def test_execution_lock_prevents_concurrency() -> None:
    plan = _confirmed_plan()
    idempotency_key = derive_idempotency_key(plan=plan)
    first = acquire_execution_lock(
        idempotency_key=idempotency_key,
        execution_id="rexec-aaa",
        session_id="lock-1",
        project=plan["project"],
        environment=plan["environment"],
        service_name=plan["service_name"],
    )
    assert first["ok"] is True
    second = acquire_execution_lock(
        idempotency_key=idempotency_key,
        execution_id="rexec-bbb",
        session_id="lock-2",
        project=plan["project"],
        environment=plan["environment"],
        service_name=plan["service_name"],
    )
    assert second["ok"] is False
    assert second["reason"] == "execution_lock_held"
    lock = load_execution_lock(idempotency_key=idempotency_key)
    assert lock is not None
    assert lock["execution_id"] == "rexec-aaa"


def test_rollback_journal_generated() -> None:
    journal = new_execution_journal(plan=_confirmed_plan(), session_id="rb-1")
    updated = attach_rollback_journal(journal)
    rollback = updated.get("rollback_journal") or {}
    assert rollback.get("rollback_id", "").startswith("rback-")
    assert len(rollback.get("actions") or []) == 5
    assert updated.get("rollback_ready") is True


def test_execution_receipts_persisted() -> None:
    journal = new_execution_journal(plan=_confirmed_plan(), session_id="rcpt-1")
    execution_id = str(journal["execution_id"])
    record_execution_receipt(execution_id=execution_id, phase="create_service", status="simulated")
    receipts = list_execution_receipts(execution_id=execution_id)
    assert len(receipts) == 1
    assert receipts[0]["mutation_performed"] is False
    assert receipts[0]["status"] == "simulated"
    from aethos_core.providers.railway.execution_contract.execution_receipts import _receipts_path

    assert _receipts_path(execution_id).is_file()


def test_execution_enabled_false_blocks_real_mutation(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
    get_settings.cache_clear()
    assert EXECUTION_ENABLED is False
    plan, preflight, simulation = _seed_ready_lane(session_id="mut-1")
    approval = assess_execution_approvals(plan=plan, preflight=preflight, simulation=simulation)
    assert approval["execution_ready"] is False
    result = request_execution_contract(plan=plan, session_id="mut-1", approval=approval)
    assert result["ok"] is True
    receipts = list_execution_receipts(execution_id=str(result["journal"]["execution_id"]))
    assert receipts
    assert all(r["mutation_performed"] is False for r in receipts)
    assert result["journal"]["mutation_enabled"] is False


def test_partial_failure_never_marks_completed() -> None:
    journal = new_execution_journal(
        plan=_confirmed_plan(),
        session_id="pf-1",
        initial_state="execution_phase_configure_env",
    )
    journal = transition_journal_state(journal, to_state="execution_partial_failure")
    assert journal["state"] == "execution_partial_failure"
    assert not can_transition(from_state="execution_partial_failure", to_state="execution_completed")
    journal["rollback_available"] = True
    journal = save_execution_journal(journal)
    assert journal["state"] != "execution_completed"


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_execution_prompts_render_correctly(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "dry_run")
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS", "staging,development,production")
    get_settings.cache_clear()
    routed = route_railway_execution_contract(
        "show railway execution contract",
        session_id="render-1",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_execution_contract_show"
    assert meta["route_id"] == "railway_execution_contract"
    assert "Execution enabled:" in body
    assert "false" in body
    assert "create_service" in body

    phases = route_railway_execution_contract("show railway execution phases", session_id="render-1")
    assert phases is not None
    assert "create_service" in phases[0]

    rollback = route_railway_execution_contract("show railway rollback contract", session_id="render-1")
    assert rollback is not None
    assert "remove_created_service" in rollback[0]

    plan = _confirmed_plan(environment="staging")
    preflight = build_creation_preflight_from_plan(plan)
    preflight["preflight_approved"] = True
    simulation = {
        "simulation_id": "rsim-render",
        "repo": plan["repo"],
        "ready_to_execute": True,
        "blocking_reasons": [],
        "blocking_reason_messages": [],
        "checks": [],
    }
    save_deployment_plan_context(session_id="render-exec", plan=plan)
    save_creation_preflight(session_id="render-exec", preflight=preflight)
    save_simulation(session_id="render-exec", simulation=simulation)
    execute = route_railway_execution_contract(
        "execute railway service creation",
        session_id="render-exec",
    )
    assert execute is not None
    assert execute[1] == "railway_execution_contract_requested"
    assert "mutation_performed: **false**" in execute[0]


def test_execute_route_reuses_journal_three_times() -> None:
    plan, preflight, simulation = _seed_ready_lane(session_id="exec-3x")
    approval = assess_execution_approvals(plan=plan, preflight=preflight, simulation=simulation)
    ids: list[str] = []
    for _ in range(3):
        result = request_execution_contract(plan=plan, session_id="exec-3x", approval=approval)
        assert result["ok"] is True
        ids.append(str(result["journal"]["execution_id"]))
    assert len(set(ids)) == 1


def test_simulated_receipts_cover_all_phases() -> None:
    plan, preflight, simulation = _seed_ready_lane(session_id="phases-1")
    approval = assess_execution_approvals(plan=plan, preflight=preflight, simulation=simulation)
    result = request_execution_contract(plan=plan, session_id="phases-1", approval=approval)
    receipts = list_execution_receipts(execution_id=str(result["journal"]["execution_id"]))
    phases = {r["phase"] for r in receipts}
    assert phases == set(EXECUTION_PHASES)


def test_rollback_contract_builder_matches_actions() -> None:
    rollback = build_rollback_journal(execution_id="rexec-test")
    action_names = [row["action"] for row in rollback["actions"]]
    assert "remove_created_service" in action_names
    assert "mark_execution_rolled_back" in action_names


def test_journal_persisted_on_disk() -> None:
    journal, _created = get_or_create_execution_journal(
        plan=_confirmed_plan(),
        session_id="disk-1",
    )
    from aethos_core.providers.railway.execution_contract.execution_journal import _journal_path

    path = _journal_path(str(journal["execution_id"]))
    assert path.is_file()
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["idempotency_key"] == journal["idempotency_key"]
