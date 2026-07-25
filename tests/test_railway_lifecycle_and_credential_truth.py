# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 99E — lifecycle truth labels and credential diagnostics."""

from __future__ import annotations

import json
from unittest.mock import patch

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
    force_materialize_latest_global_lifecycle,
    inspect_all_global_lifecycle_entries,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
    compose_no_plan_after_lifecycle_ensure,
    is_fresh_runtime_lifecycle_state,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    _index_path,
    _store_dir,
    clear_for_tests as clear_lifecycle,
    save_lifecycle_record,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight import build_creation_preflight_from_plan
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import compose_readiness_blocker
from aethos_core.providers.railway.deployment_readiness.railway_credential_diagnostics import (
    diagnose_railway_credential_resolution,
    format_railway_credential_diagnostics_report,
    route_railway_credential_diagnostics,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)


def setup_function() -> None:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
        clear_for_tests as clear_readiness,
    )

    clear_lifecycle()
    clear_readiness()


def _confirmed_plan() -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-99e",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
            "mutation_ready": True,
        }
    )


def _lifecycle_record(*, session_id: str, include_plan_snapshot: bool = True) -> dict:
    plan = _confirmed_plan()
    preflight = build_creation_preflight_from_plan(plan)
    return {
        "lifecycle_id": "rlc-99e",
        "session_id": session_id,
        "repo": plan["repo"],
        "project": plan["project"],
        "environment": plan["environment"],
        "service_name": plan["service_name"],
        "plan": {
            "exists": True,
            "mutation_ready": True,
            "review_confirmed": True,
            "snapshot": dict(plan) if include_plan_snapshot else {},
        },
        "preflight": {
            "exists": True,
            "preflight_id": preflight["preflight_id"],
            "snapshot": dict(preflight),
        },
        "simulation": {"exists": False, "snapshot": {}},
    }


def test_index_with_entries_is_not_fresh_runtime() -> None:
    save_lifecycle_record(session_id="99e-orig", record=_lifecycle_record(session_id="99e-orig"))
    assert is_fresh_runtime_lifecycle_state() is False


def test_index_with_entries_no_plan_shows_materialization_failure_not_fresh() -> None:
    _store_dir()
    _index_path().write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "lifecycle_id": "rlc-ghost",
                        "session_id": "ghost",
                        "repo": "pilotmain/aethos",
                        "updated_at": "2026-05-26T00:00:00Z",
                        "active": True,
                    }
                ],
                "latest_lifecycle_id": "rlc-ghost",
                "latest_by_repo": {"pilotmain/aethos": "rlc-ghost"},
            }
        ),
        encoding="utf-8",
    )
    body = compose_no_plan_after_lifecycle_ensure(ensure_result="miss", session_id="99e-stale")
    assert "fresh runtime state" not in body.lower()
    assert "no usable deployment plan could be materialized" in body.lower()
    assert "stale_index_missing_file" in body or "lifecycle file is missing" in body.lower()


def test_missing_plan_snapshot_exact_message() -> None:
    save_lifecycle_record(
        session_id="99e-nosnap",
        record=_lifecycle_record(session_id="99e-nosnap", include_plan_snapshot=False),
    )
    result = force_materialize_latest_global_lifecycle(session_id="99e-target")
    assert result["ok"] is False
    assert result["reason"] == "plan_snapshot_missing"
    entries = inspect_all_global_lifecycle_entries()
    assert entries[0]["plan_snapshot_present"] is False


@patch("aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks")
def test_simulator_auto_materialization_failure_includes_index_diagnostics(mock_checks) -> None:
    mock_checks.return_value = [{"check": "execution_api_surface", "status": "blocked"}]
    _store_dir()
    _index_path().write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "lifecycle_id": "rlc-ghost2",
                        "session_id": "ghost2",
                        "repo": "pilotmain/aethos",
                        "updated_at": "2026-05-26T00:00:00Z",
                        "active": True,
                    }
                ],
                "latest_lifecycle_id": "rlc-ghost2",
                "latest_by_repo": {},
            }
        ),
        encoding="utf-8",
    )
    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="99e-sim-fail",
    )
    assert result is not None
    body, _intent, _meta = result
    assert "fresh runtime state" not in body.lower()
    assert "Entry 1:" in body or "lifecycle file exists" in body


def test_readiness_token_fail_includes_debug_command_hint() -> None:
    checks = {
        "readonly_readiness_ok": False,
        "railway_credential_ok": False,
        "railway_credential_source": "canonical provider credential resolver",
        "inventory": {"ok": False, "error": "skipped"},
        "github_binding": {"github_credential_ok": True},
        "service_creation": {},
        "required_env_vars": ["RAILWAY_API_TOKEN"],
    }
    body = compose_readiness_blocker(checks)
    assert "Railway token: **fail**" in body
    assert "debug railway credential resolution" in body


@patch("aethos_core.providers.railway.credential_truth.list_services_with_status")
def test_credential_debug_never_prints_token(mock_inventory_probe) -> None:
    mock_inventory_probe.return_value = {
        "ok": True,
        "services": [{"name": "svc", "project_name": "p1"}],
        "error": None,
    }
    diag = diagnose_railway_credential_resolution()
    body = format_railway_credential_diagnostics_report(diag)
    assert "secret-token-value" not in body
    assert "railway.credential_truth.resolve_railway_credential" in body
    routed = route_railway_credential_diagnostics(
        "debug railway credential resolution",
        session_id="99e-cred",
    )
    assert routed is not None
    assert "secret-token-value" not in routed[0]
