# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 99D — Railway lifecycle index materialization failures."""

from __future__ import annotations

import json
from unittest.mock import patch

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
    force_materialize_latest_global_lifecycle,
    inspect_all_global_lifecycle_entries,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_repair import (
    format_lifecycle_repair_report,
    repair_railway_deployment_lifecycle,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
    compose_session_lifecycle_materialization_failed_reply,
    ensure_railway_deployment_lifecycle_for_lane,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    _index_path,
    _session_path,
    _store_dir,
    clear_for_tests as clear_lifecycle,
    clear_stale_global_lifecycle_index,
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
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
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
            "plan_id": "plan-99d",
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


def _lifecycle_record(*, session_id: str, include_plan_snapshot: bool = True) -> dict:
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    snapshot = dict(plan) if include_plan_snapshot else {}
    return {
        "lifecycle_id": "rlc-99d",
        "session_id": session_id,
        "repo": plan["repo"],
        "branch": plan["branch"],
        "project": plan["project"],
        "environment": plan["environment"],
        "service_name": plan["service_name"],
        "plan": {
            "exists": True,
            "mutation_ready": True,
            "review_confirmed": True,
            "snapshot": snapshot,
        },
        "preflight": {
            "exists": True,
            "preflight_id": preflight["preflight_id"],
            "approved": False,
            "snapshot": dict(preflight),
        },
        "simulation": {"exists": False, "snapshot": {}},
    }


def test_global_index_auto_materializes_plan_into_new_session() -> None:
    save_lifecycle_record(session_id="99d-orig", record=_lifecycle_record(session_id="99d-orig"))
    _CONTEXT_STORE.clear()

    result = force_materialize_latest_global_lifecycle(session_id="99d-new")
    assert result["ok"] is True
    assert result["materialized"]["deployment_plan"] is True
    plan = get_deployment_plan_context(session_id="99d-new")
    assert plan is not None
    assert plan.get("repo") == "pilotmain/aethos"
    assert _session_path("99d-new").is_file()


def test_stale_index_entry_missing_file_reports_precisely() -> None:
    _store_dir()
    _index_path().write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "lifecycle_id": "rlc-missing",
                        "session_id": "ghost-session",
                        "repo": "pilotmain/aethos",
                        "updated_at": "2026-05-26T00:00:00Z",
                        "active": True,
                    }
                ],
                "latest_lifecycle_id": "rlc-missing",
                "latest_by_repo": {"pilotmain/aethos": "rlc-missing"},
            }
        ),
        encoding="utf-8",
    )
    result = force_materialize_latest_global_lifecycle(session_id="99d-stale")
    assert result["ok"] is False
    assert result["reason"] == "stale_index"
    body = compose_session_lifecycle_materialization_failed_reply(
        ensure_result="miss",
        materialization=result,
    )
    assert "lifecycle file is missing" in body
    assert "clear stale railway lifecycle index" in body


def test_missing_plan_snapshot_reports_precise_blocker() -> None:
    save_lifecycle_record(
        session_id="99d-nosnap",
        record=_lifecycle_record(session_id="99d-nosnap", include_plan_snapshot=False),
    )
    entries = inspect_all_global_lifecycle_entries()
    assert entries
    assert entries[0]["plan_snapshot_present"] is False
    result = force_materialize_latest_global_lifecycle(session_id="99d-nosnap-target")
    assert result["ok"] is False
    assert result["reason"] == "plan_snapshot_missing"


def test_repair_materializes_and_reread_succeeds() -> None:
    save_lifecycle_record(session_id="99d-repair-orig", record=_lifecycle_record(session_id="99d-repair-orig"))
    _CONTEXT_STORE.clear()
    result = repair_railway_deployment_lifecycle(session_id="99d-repair-new")
    report = format_lifecycle_repair_report(result)
    assert result["ok"] is True
    assert "Materialized:" in report
    assert get_deployment_plan_context(session_id="99d-repair-new") is not None


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_simulator_uses_repaired_session_without_manual_restart(mock_checks) -> None:
    mock_checks.return_value = [
        {"check": "railway_credential_readiness", "status": "pass"},
        {"check": "required_env_var_readiness", "status": "blocked", "env_var_values_status": "blocked"},
        {"check": "execution_api_surface", "status": "blocked"},
    ]
    save_lifecycle_record(session_id="99d-sim-orig", record=_lifecycle_record(session_id="99d-sim-orig"))
    _CONTEXT_STORE.clear()
    repair = repair_railway_deployment_lifecycle(session_id="99d-sim-new")
    assert repair["ok"] is True

    routed = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="99d-sim-new",
    )
    assert routed is not None
    body, intent, _meta = routed
    assert intent == "railway_service_creation_simulation"
    assert "could not load a Railway deployment plan" not in body


def test_ensure_lane_auto_materializes_from_global_index() -> None:
    save_lifecycle_record(session_id="99d-ensure-orig", record=_lifecycle_record(session_id="99d-ensure-orig"))
    _CONTEXT_STORE.clear()
    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id="99d-ensure-new",
        require_plan=True,
    )
    assert lane.plan is not None
    assert lane.plan.get("repo") == "pilotmain/aethos"
    assert lane.ensure_result in {"hit", "partial"}


def test_clear_stale_index() -> None:
    _store_dir()
    _index_path().write_text(
        json.dumps(
            {
                "entries": [{"lifecycle_id": "rlc-x", "session_id": "x", "repo": "a/b", "active": True}],
                "latest_lifecycle_id": "rlc-x",
                "latest_by_repo": {},
            }
        ),
        encoding="utf-8",
    )
    cleared = clear_stale_global_lifecycle_index()
    assert cleared["cleared"] is True
    assert cleared["removed_entries"] == 1
