# SPDX-License-Identifier: Apache-2.0
"""FIX 102 — Railway greenfield execution enablement boundary."""

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
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    NON_PRODUCTION_FINAL_PHRASE,
    PRODUCTION_FINAL_PHRASE,
    assess_railway_execution_enablement_policy,
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


def _patch_enablement(monkeypatch, **overrides: str) -> None:
    defaults = {
        "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "false",
        "RAILWAY_GREENFIELD_EXECUTION_MODE": "disabled",
        "RAILWAY_GREENFIELD_ALLOWED_PROJECTS": "pilotos",
        "RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS": "staging,development",
        "RAILWAY_GREENFIELD_ALLOW_PRODUCTION": "false",
        "RAILWAY_GREENFIELD_ALLOWED_SERVICES": "",
        "RAILWAY_GREENFIELD_REQUIRE_FINAL_PHRASE": "true",
    }
    for key, value in {**defaults, **overrides}.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()


def _production_plan(*, project: str = "pilotos", environment: str = "production") -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-102",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": project,
            "environment": environment,
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["OPENAI_API_KEY"],
            "mutation_ready": True,
        }
    )


def _seed_lane(session_id: str, plan: dict) -> None:
    preflight = build_creation_preflight_from_plan(plan)
    preflight["preflight_approved"] = True
    simulation = {
        "simulation_id": "rsim-102",
        "repo": plan["repo"],
        "ready_to_execute": True,
        "blocking_reasons": [],
        "blocking_reason_messages": [],
        "checks": [],
    }
    save_deployment_plan_context(session_id=session_id, plan=plan)
    save_creation_preflight(session_id=session_id, preflight=preflight)
    save_simulation(session_id=session_id, simulation=simulation)


def test_default_disabled_blocks_execution(monkeypatch) -> None:
    _patch_enablement(monkeypatch)
    plan = _production_plan()
    policy = assess_railway_execution_enablement_policy(plan=plan)
    assert policy.mode == "disabled"
    assert policy.allowed is False
    assert policy.allows_execute_enrollment() is False
    assert "execution_mode_disabled" in policy.blocking_reasons


def test_no_target_shows_none_loaded_without_allowlist_blockers(monkeypatch) -> None:
    _patch_enablement(monkeypatch)
    policy = assess_railway_execution_enablement_policy(plan={})
    assert policy.target_loaded is False
    assert "no_target_loaded" in policy.blocking_reasons
    assert "project_not_allowlisted" not in policy.blocking_reasons
    assert "environment_not_allowlisted" not in policy.blocking_reasons
    assert not any("allowlist" in msg.lower() for msg in policy.blocking_reason_messages)

    routed = route_railway_execution_contract(
        "show railway execution enablement",
        session_id="102b-no-target",
    )
    assert routed is not None
    body, intent, _meta = routed
    assert intent == "railway_execution_enablement"
    assert "Current target:" in body
    assert "- none loaded" in body
    assert "No Railway deployment target is loaded." in body
    assert "Railway greenfield execution mode is disabled" in body
    assert "Next step:" in body
    assert "create railway deployment plan for <repo> in <project> / <environment>" in body
    assert "Project `" not in body
    assert "Environment `" not in body


def test_target_not_allowlisted_shows_real_blockers(monkeypatch) -> None:
    _patch_enablement(
        monkeypatch,
        RAILWAY_GREENFIELD_EXECUTION_MODE="enabled",
        RAILWAY_GREENFIELD_ALLOWED_PROJECTS="other-project",
    )
    plan = _production_plan(project="pilotos", environment="staging")
    policy = assess_railway_execution_enablement_policy(plan=plan)
    assert policy.target_loaded is True
    assert "project_not_allowlisted" in policy.blocking_reasons
    assert any("Project `pilotos` is not in the greenfield execution allowlist." in msg for msg in policy.blocking_reason_messages)


def test_show_enablement_prompt_default(monkeypatch) -> None:
    _patch_enablement(monkeypatch)
    plan = _production_plan()
    save_deployment_plan_context(session_id="102-show", plan=plan)
    routed = route_railway_execution_contract(
        "show railway execution enablement",
        session_id="102-show",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_execution_enablement"
    assert meta["mutation_performed"] == "false"
    assert meta["execution_mode"] == "disabled"
    assert meta["policy_allowed"] == "false"
    assert meta["production_allowed"] == "false"
    assert meta["final_phrase_required"] == "true"
    assert "# Railway Execution Enablement" in body
    assert "Mode:" in body and "**disabled**" in body
    assert "greenfield execution enabled: **false**" in body
    assert "allowed projects: pilotos" in body
    assert "allowed environments: staging, development" in body
    assert "production allowed: **false**" in body
    assert "project: pilotos" in body
    assert "environment: production" in body
    assert "service: aethos-api" in body
    assert "allowed: **false**" in body
    assert "Railway greenfield execution mode is disabled" in body
    assert "Production greenfield execution is not allowed" in body
    assert "No Railway mutation has been performed." in body


def test_dry_run_allows_simulated_enrollment_not_real_mutation(monkeypatch) -> None:
    _patch_enablement(
        monkeypatch,
        RAILWAY_GREENFIELD_EXECUTION_MODE="dry_run",
    )
    plan = _production_plan(environment="staging")
    policy = assess_railway_execution_enablement_policy(plan=plan)
    assert policy.mode == "dry_run"
    assert policy.allows_execute_enrollment() is True
    assert policy.allows_real_mutation() is False


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_enabled_project_not_allowlisted_blocks(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_enablement(
        monkeypatch,
        RAILWAY_GREENFIELD_EXECUTION_MODE="enabled",
        RAILWAY_GREENFIELD_ALLOWED_PROJECTS="other-project",
    )
    plan = _production_plan(environment="staging")
    policy = assess_railway_execution_enablement_policy(plan=plan)
    assert policy.allows_execute_enrollment() is False
    assert "project_not_allowlisted" in policy.blocking_reasons


def test_enabled_production_not_allowed_blocks(monkeypatch) -> None:
    _patch_enablement(
        monkeypatch,
        RAILWAY_GREENFIELD_EXECUTION_MODE="enabled",
        RAILWAY_GREENFIELD_ALLOW_PRODUCTION="false",
    )
    plan = _production_plan()
    policy = assess_railway_execution_enablement_policy(plan=plan)
    assert policy.allows_execute_enrollment() is False
    assert "production_not_allowed" in policy.blocking_reasons


def test_final_phrase_required_and_missing_blocks(monkeypatch) -> None:
    _patch_enablement(
        monkeypatch,
        RAILWAY_GREENFIELD_EXECUTION_MODE="enabled",
        RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS="staging,development,production",
        RAILWAY_GREENFIELD_ALLOW_PRODUCTION="true",
    )
    plan = _production_plan(environment="staging")
    policy = assess_railway_execution_enablement_policy(plan=plan, user_text="execute please")
    assert "final_phrase_missing" in policy.blocking_reasons
    assert policy.allows_execute_enrollment() is False


def test_exact_final_phrase_passes_policy_but_no_mutation(monkeypatch) -> None:
    _patch_enablement(
        monkeypatch,
        RAILWAY_GREENFIELD_EXECUTION_MODE="enabled",
        RAILWAY_GREENFIELD_EXECUTION_ENABLED="true",
        RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS="staging,development,production",
        RAILWAY_GREENFIELD_ALLOW_PRODUCTION="true",
    )
    plan = _production_plan(environment="staging")
    policy = assess_railway_execution_enablement_policy(
        plan=plan,
        user_text=NON_PRODUCTION_FINAL_PHRASE,
    )
    assert policy.final_phrase_valid is True
    assert policy.allows_execute_enrollment() is True
    assert policy.allows_real_mutation() is True


def test_production_final_phrase_exact_match(monkeypatch) -> None:
    _patch_enablement(
        monkeypatch,
        RAILWAY_GREENFIELD_EXECUTION_MODE="enabled",
        RAILWAY_GREENFIELD_EXECUTION_ENABLED="true",
        RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS="production,staging",
        RAILWAY_GREENFIELD_ALLOW_PRODUCTION="true",
    )
    plan = _production_plan()
    policy = assess_railway_execution_enablement_policy(
        plan=plan,
        user_text=PRODUCTION_FINAL_PHRASE,
    )
    assert policy.final_phrase_valid is True
    assert policy.allows_real_mutation() is True


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_execution_gate_includes_policy_result(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_enablement(monkeypatch)
    plan = _production_plan()
    _seed_lane("102-gate", plan)
    preflight = get_creation_preflight(session_id="102-gate")
    simulation = get_simulation(session_id="102-gate")
    gate = evaluate_railway_execution_readiness(
        "102-gate",
        plan=plan,
        preflight=preflight,
        simulation=simulation,
    )
    assert gate.checks["execution_policy"] == "fail"
    assert gate.enablement is not None
    assert gate.enablement.mode == "disabled"
    assert any(
        "Railway greenfield execution mode is disabled" in msg
        for msg in gate.blocking_reason_messages
    )
    assert any(
        "Production greenfield execution is not allowed by runtime policy" in msg
        for msg in gate.blocking_reason_messages
    )


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_execute_blocked_when_mode_disabled(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_enablement(monkeypatch)
    plan = _production_plan()
    _seed_lane("102-exec-block", plan)
    routed = route_railway_execution_contract(
        "execute railway service creation",
        session_id="102-exec-block",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_execution_contract_not_ready"
    assert meta["mutation_performed"] == "false"
    assert meta["execution_mode"] == "disabled"
    assert "Railway greenfield execution mode is disabled" in body


@patch("aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence")
def test_no_railway_mutation_performed(mock_probe, monkeypatch) -> None:
    mock_probe.return_value = {"present": True, "secret": False, "source": "configured"}
    _patch_enablement(
        monkeypatch,
        RAILWAY_GREENFIELD_EXECUTION_MODE="dry_run",
    )
    plan = _production_plan(environment="staging")
    _seed_lane("102-dry", plan)
    routed = route_railway_execution_contract(
        "show railway execution enablement",
        session_id="102-dry",
    )
    assert routed is not None
    body, intent, meta = routed
    assert meta["mutation_performed"] == "false"
    assert "No Railway mutation has been performed." in body
