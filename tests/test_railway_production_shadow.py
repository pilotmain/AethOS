# SPDX-License-Identifier: Apache-2.0
"""FIX 118 — production shadow rehearsal orchestration."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    PRODUCTION_FINAL_PHRASE,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    bind_session_execution,
    clear_for_tests as clear_execution_context,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
    get_or_create_execution_journal,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    PRODUCTION_QUORUM_CONFIRMATION_PHRASE,
    record_production_confirmations_from_text,
)
from aethos_core.providers.railway.execution_contract.production_shadow_contract_models import (
    FORWARD_SHADOW_PHASES,
    ROLLBACK_SHADOW_PHASES,
)
from aethos_core.providers.railway.execution_contract.production_shadow_executor import (
    assert_shadow_executor_isolation,
    run_production_shadow_forward,
    run_production_shadow_rollback,
)
from aethos_core.providers.railway.execution_contract.production_shadow_gate import (
    assess_production_shadow_gate,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    clear_for_tests as clear_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_shadow_receipts import (
    clear_for_tests as clear_shadow_receipts,
    list_shadow_receipts,
)
from aethos_core.providers.railway.execution_contract.production_shadow_router import (
    is_railway_production_shadow_intent,
    route_railway_production_shadow,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_journal()
    clear_shadow_receipts()
    clear_shadow_journal()
    clear_execution_context()
    get_settings.cache_clear()
    yield
    clear_journal()
    clear_shadow_receipts()
    clear_shadow_journal()
    clear_execution_context()
    get_settings.cache_clear()


def _prod_plan() -> dict:
    return {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "production",
        "service_name": "api",
        "branch": "main",
    }


def _enable_shadow(monkeypatch):
    monkeypatch.setenv("RAILWAY_PRODUCTION_SHADOW_EXECUTION", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOW_PRODUCTION", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS", "staging,development,production")
    get_settings.cache_clear()


def _seed_execution(session: str, plan: dict) -> str:
    journal, _ = get_or_create_execution_journal(
        plan=plan,
        session_id=session,
        initial_state="simulation_complete",
        approval={},
    )
    execution_id = str(journal["execution_id"])
    bind_session_execution(session_id=session, execution_id=execution_id)
    return execution_id


def test_shadow_intents():
    assert is_railway_production_shadow_intent("simulate production railway deployment")
    assert is_railway_production_shadow_intent("show railway production shadow status")


def test_shadow_executor_isolation():
    assert assert_shadow_executor_isolation() is True


def test_incident_mode_blocks_shadow_forward(monkeypatch):
    _enable_shadow(monkeypatch)
    monkeypatch.setenv("RAILWAY_PRODUCTION_INCIDENT_MODE", "true")
    get_settings.cache_clear()
    execution_id = _seed_execution("shadow-incident", _prod_plan())
    gate = assess_production_shadow_gate(
        plan=_prod_plan(),
        user_text=PRODUCTION_FINAL_PHRASE,
        execution_id=execution_id,
    )
    assert gate.ready is False
    assert "production_incident_mode_active" in gate.blockers


def test_full_shadow_forward_and_rollback_lifecycle(monkeypatch):
    _enable_shadow(monkeypatch)
    plan = _prod_plan()
    execution_id = _seed_execution("shadow-full", plan)
    phrase_text = f"{PRODUCTION_FINAL_PHRASE}\n{PRODUCTION_QUORUM_CONFIRMATION_PHRASE}"
    record_production_confirmations_from_text(execution_id=execution_id, user_text=phrase_text)

    forward = run_production_shadow_forward(
        execution_id=execution_id,
        plan=plan,
        user_text=phrase_text,
    )
    assert forward.policy_blocked is False
    assert forward.shadow_completed is True
    assert len(forward.executed_phases) == len(FORWARD_SHADOW_PHASES)

    receipts = list_shadow_receipts(execution_id=execution_id)
    assert len(receipts) >= len(FORWARD_SHADOW_PHASES)
    assert all(r.get("mutation_performed") is False for r in receipts)
    assert all(r.get("execution_mode") == "production_shadow" for r in receipts)

    rollback = run_production_shadow_rollback(
        execution_id=execution_id,
        plan=plan,
        user_text=phrase_text,
    )
    assert rollback.shadow_completed is True
    all_receipts = list_shadow_receipts(execution_id=execution_id)
    phases = {str(r.get("phase")) for r in all_receipts}
    for phase in ROLLBACK_SHADOW_PHASES:
        assert phase in phases
    assert "rollback_shadow" in phases


def test_shadow_disabled_blocks(monkeypatch):
    monkeypatch.setenv("RAILWAY_PRODUCTION_SHADOW_EXECUTION", "false")
    get_settings.cache_clear()
    gate = assess_production_shadow_gate(plan=_prod_plan(), user_text=PRODUCTION_FINAL_PHRASE)
    assert "production_shadow_execution_disabled" in gate.blockers


def test_show_shadow_status_route(monkeypatch):
    _enable_shadow(monkeypatch)
    routed = route_railway_production_shadow(
        "show railway production freeze status",
        session_id="shadow-route-freeze",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_production_freeze_status"
    assert meta["route_id"] == "railway_production_shadow"
    assert "freeze" in body.lower()
