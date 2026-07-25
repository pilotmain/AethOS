# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 98J — simulator/preflight auto-hydrate Railway deployment lifecycle."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_diagnostics_router import (
    route_railway_deployment_lifecycle_diagnostics,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests as clear_lifecycle,
    save_lifecycle_record,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight import build_creation_preflight_from_plan
from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    clear_for_tests as clear_preflight,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight_router import (
    route_railway_service_creation_preflight,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    _CONTEXT_STORE,
    clear_for_tests as clear_plan,
    get_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
    clear_for_tests as clear_sim,
    get_simulation,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)


def setup_function() -> None:
    clear_plan()
    clear_preflight()
    clear_sim()
    clear_lifecycle()


def _confirmed_plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-98j",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["APP_ENV"],
            "mutation_ready": True,
        }
    )


def _full_lifecycle_record(*, session_id: str, include_simulation: bool = False) -> dict:
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    record = {
        "lifecycle_id": "rlc-98j",
        "session_id": session_id,
        "repo": plan["repo"],
        "branch": plan["branch"],
        "project": plan["project"],
        "environment": plan["environment"],
        "service_name": plan["service_name"],
        "readiness": {"status": "passed", "checked_at": "2026-05-26T00:00:00Z", "checks": {}},
        "plan": {
            "exists": True,
            "mutation_ready": True,
            "review_confirmed": True,
            "snapshot": dict(plan),
        },
        "preflight": {
            "exists": True,
            "preflight_id": preflight["preflight_id"],
            "approved": False,
            "snapshot": dict(preflight),
        },
        "simulation": {"exists": False, "ready_to_execute": False, "blocking_reasons": [], "snapshot": {}},
    }
    if include_simulation:
        record["simulation"] = {
            "exists": True,
            "ready_to_execute": False,
            "blocking_reasons": ["env_values_not_configured", "greenfield_service_creation_not_wired"],
            "snapshot": {
                "simulation_id": "rsim-98j-global",
                "repo": plan["repo"],
                "project": plan["project"],
                "environment": plan["environment"],
                "service_name": plan["service_name"],
                "branch": plan["branch"],
                "ready_to_execute": False,
                "blocking_reasons": ["env_values_not_configured", "greenfield_service_creation_not_wired"],
                "blocking_reason_messages": [
                    "Required env var values have not been supplied through a secure credential path.",
                    "Railway greenfield service creation mutation is not wired yet.",
                ],
                "checks": [
                    {
                        "check": "railway_credential_readiness",
                        "status": "pass",
                        "canonical_token_present": True,
                        "credential_source": "canonical provider credential resolver",
                    },
                    {"check": "execution_api_surface", "status": "blocked"},
                ],
            },
        }
    return record


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_simulator_auto_materializes_plan_from_lifecycle_global_index(mock_checks) -> None:
    mock_checks.return_value = [
        {"check": "railway_project_environment", "status": "pass"},
        {"check": "service_name_availability", "status": "pass"},
        {"check": "github_source_binding", "status": "pass"},
        {"check": "railway_credential_readiness", "status": "pass", "canonical_token_present": True},
        {
            "check": "required_env_var_readiness",
            "status": "blocked",
            "env_var_values_status": "blocked",
        },
        {"check": "execution_api_surface", "status": "blocked"},
    ]
    save_lifecycle_record(session_id="98j-orig", record=_full_lifecycle_record(session_id="98j-orig"))
    _CONTEXT_STORE.clear()

    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="98j-new",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_service_creation_simulation"
    assert "don't have a saved Railway deployment plan" not in body
    assert meta.get("hydrated_from_global_lifecycle") == "true"
    assert meta.get("mutation_performed") == "false"
    plan = get_deployment_plan_context(session_id="98j-new")
    assert plan is not None
    assert plan.get("repo") == "pilotmain/aethos"


@patch("aethos_core.credentials.get_provider_api_token")
def test_blocking_followup_auto_materializes_simulation_from_lifecycle(mock_token) -> None:
    mock_token.return_value = "railway-token"
    save_lifecycle_record(
        session_id="98j-block-orig",
        record=_full_lifecycle_record(session_id="98j-block-orig", include_simulation=True),
    )
    _CONTEXT_STORE.clear()
    clear_sim()

    result = route_railway_service_creation_simulator(
        "what is blocking execution?",
        session_id="98j-block-new",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_service_creation_simulation_blocking"
    assert "Railway credential or readonly inventory is not ready" not in body
    assert meta.get("lifecycle_ensure_called") == "true"
    assert "env var values" in body.lower()
    assert meta.get("hydrated_from_global_lifecycle") == "true"
    stored = get_simulation(session_id="98j-block-new")
    assert stored is not None
    assert stored.get("simulation_id") == "rsim-98j-global"


def test_preflight_auto_materializes_confirmed_plan() -> None:
    save_lifecycle_record(session_id="98j-pref-orig", record=_full_lifecycle_record(session_id="98j-pref-orig"))
    _CONTEXT_STORE.clear()

    result = route_railway_service_creation_preflight(
        "create railway service creation preflight",
        session_id="98j-pref-new",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_creation_preflight_draft"
    assert "don't have a saved Railway deployment plan" not in body
    assert meta.get("hydrated_from_global_lifecycle") == "true"
    assert meta.get("mutation_performed") == "false"


def test_manual_repair_still_works() -> None:
    save_lifecycle_record(session_id="98j-repair-orig", record=_full_lifecycle_record(session_id="98j-repair-orig"))
    _CONTEXT_STORE.clear()

    result = route_railway_deployment_lifecycle_diagnostics(
        "repair railway deployment lifecycle",
        session_id="98j-repair-new",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_deployment_lifecycle_repair"
    assert "Repaired Railway deployment lifecycle" in body
    assert meta.get("mutation_performed") == "false"
    plan = get_deployment_plan_context(session_id="98j-repair-new")
    assert plan is not None
