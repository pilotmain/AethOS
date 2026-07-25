# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 98H — Railway deployment lifecycle diagnostics and repair."""

from __future__ import annotations

import json
from unittest.mock import patch

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_diagnostics import (
    format_lifecycle_diagnostics_report,
    trace_railway_deployment_lifecycle_resolution,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_diagnostics_router import (
    route_railway_deployment_lifecycle_diagnostics,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_repair import (
    repair_railway_deployment_lifecycle,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    _index_path,
    _session_path,
    _store_dir,
    clear_for_tests as clear_lifecycle,
    inspect_global_lifecycle_index,
    save_lifecycle_record,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight import build_creation_preflight_from_plan
from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    clear_for_tests as clear_preflight,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    _CONTEXT_STORE,
    clear_for_tests as clear_plan,
    get_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.deployment_plan.deployment_plan_lifecycle import compose_no_plan_reply
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)


def setup_function() -> None:
    clear_plan()
    clear_preflight()
    clear_lifecycle()


def _confirmed_plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-98h",
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


def _lifecycle_record(*, session_id: str) -> dict:
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    return {
        "lifecycle_id": "rlc-98h-test",
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


def test_debug_shows_index_hit_when_session_file_missing() -> None:
    save_lifecycle_record(session_id="orig-98h", record=_lifecycle_record(session_id="orig-98h"))
    assert _session_path("orig-98h").is_file()
    assert not _session_path("new-98h").is_file()

    trace = trace_railway_deployment_lifecycle_resolution(session_id="new-98h", user_text="")
    report = format_lifecycle_diagnostics_report(trace)

    assert trace["session_file_exists"] is False
    assert trace["index"]["exists"] is True
    assert trace["index"]["entries"] >= 1
    assert any(a["source"] == "latest_active_global" and a["result"] == "hit" for a in trace["attempts"])
    assert "Railway deployment lifecycle diagnostics" in report
    assert "pilotmain/aethos" in report
    assert "No mutation." in report


def test_repair_materializes_plan_into_session() -> None:
    save_lifecycle_record(session_id="repair-orig", record=_lifecycle_record(session_id="repair-orig"))
    _CONTEXT_STORE.clear()

    result = repair_railway_deployment_lifecycle(session_id="repair-new")
    assert result["ok"] is True
    assert result["plan_found"] is True
    assert _session_path("repair-new").is_file()
    plan = get_deployment_plan_context(session_id="repair-new")
    assert plan is not None
    assert plan.get("repo") == "pilotmain/aethos"


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_simulator_works_after_repair(mock_checks) -> None:
    mock_checks.return_value = [
        {"check": "railway_credential_readiness", "status": "pass"},
        {"check": "required_env_var_readiness", "status": "blocked", "env_var_values_status": "blocked"},
        {"check": "execution_api_surface", "status": "blocked"},
    ]
    save_lifecycle_record(session_id="sim-orig", record=_lifecycle_record(session_id="sim-orig"))
    _CONTEXT_STORE.clear()

    repair = repair_railway_deployment_lifecycle(session_id="sim-new")
    assert repair["ok"] is True

    routed = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="sim-new",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_service_creation_simulation"
    assert "don't have a saved Railway deployment plan" not in body
    assert meta.get("mutation_performed") == "false"


def test_corrupted_global_index_returns_readable_error_not_crash() -> None:
    _store_dir()
    _index_path().write_text("{not-json", encoding="utf-8")
    inspected = inspect_global_lifecycle_index()
    assert inspected["exists"] is True
    assert inspected["readable"] is False
    assert inspected["error"]

    routed = route_railway_deployment_lifecycle_diagnostics(
        "show railway deployment lifecycle",
        session_id="corrupt-index",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_deployment_lifecycle_diagnostics"
    assert "readable: **no**" in body
    assert meta.get("mutation_performed") == "false"


def test_repair_route_no_mutation() -> None:
    save_lifecycle_record(session_id="route-orig", record=_lifecycle_record(session_id="route-orig"))
    routed = route_railway_deployment_lifecycle_diagnostics(
        "repair railway deployment lifecycle",
        session_id="route-new",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_deployment_lifecycle_repair"
    assert "Repaired Railway deployment lifecycle" in body
    assert "Materialized:" in body
    assert "No mutation has been performed" in body
    assert meta.get("mutation_performed") == "false"


def test_no_plan_reply_includes_lifecycle_hints() -> None:
    body = compose_no_plan_reply()
    assert "in this session" in body
    assert "show railway deployment lifecycle" in body
    assert "repair railway deployment lifecycle" in body


def test_repair_fails_gracefully_on_empty_index() -> None:
    _store_dir()
    _index_path().write_text(json.dumps({"entries": [], "latest_lifecycle_id": "", "latest_by_repo": {}}), encoding="utf-8")
    result = repair_railway_deployment_lifecycle(session_id="empty-index")
    assert result["ok"] is False
    routed = route_railway_deployment_lifecycle_diagnostics(
        "repair railway deployment lifecycle",
        session_id="empty-index",
    )
    assert routed is not None
    body, intent, _meta = routed
    assert intent == "railway_deployment_lifecycle_repair_failed"
    assert "No mutation has been performed" in body
