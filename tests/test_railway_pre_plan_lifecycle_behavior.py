# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 99F — readiness-only pre_plan lifecycle must not block plan creation or simulator."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_diagnostics import (
    format_lifecycle_diagnostics_report,
    trace_railway_deployment_lifecycle_resolution,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_diagnostics_router import (
    route_railway_deployment_lifecycle_diagnostics,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
    force_materialize_latest_global_lifecycle,
    inspect_all_global_lifecycle_entries,
    is_readiness_only_lifecycle,
    load_best_global_lifecycle_record,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_repair import (
    format_lifecycle_repair_report,
    repair_railway_deployment_lifecycle,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
    lifecycle_plan_snapshot,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
    compose_no_plan_after_lifecycle_ensure,
    ensure_railway_deployment_lifecycle_for_lane,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests as clear_lifecycle,
    get_lifecycle_session,
    save_lifecycle_record,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    _CONTEXT_STORE,
    clear_for_tests as clear_plan,
    get_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_router import (
    route_railway_new_service_plan,
)
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
    clear_for_tests as clear_readiness,
    get_readiness_context,
    save_readiness_context,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)


def setup_function() -> None:
    clear_plan()
    clear_readiness()
    clear_lifecycle()


def _passed_readiness_checks() -> dict:
    return {
        "readonly_readiness_ok": True,
        "mutation_ready": False,
        "railway_credential_ok": True,
        "referenced_github_repo": "pilotmain/aethos",
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": True, "project_count": 1, "environment_count": 1, "service_count": 1, "projects": []},
        "github_binding": {"github_credential_ok": True},
        "service_creation": {"graphql_service_create": False},
    }


def _readiness_only_lifecycle(*, session_id: str) -> dict:
    return {
        "lifecycle_id": "rlc-99f-preplan",
        "session_id": session_id,
        "repo": "pilotmain/aethos",
        "branch": "main",
        "project": "",
        "environment": "",
        "service_name": "",
        "readiness": {
            "status": "passed",
            "checked_at": "2026-05-26T12:00:00Z",
            "checks": _passed_readiness_checks(),
        },
        "plan": {
            "exists": False,
            "mutation_ready": False,
            "review_confirmed": False,
            "snapshot": {},
        },
        "preflight": {"exists": False, "preflight_id": "", "approved": False, "snapshot": {}},
        "simulation": {"exists": False, "ready_to_execute": False, "blocking_reasons": [], "snapshot": {}},
    }


def test_readiness_creates_pre_plan_lifecycle_with_no_plan_snapshot() -> None:
    save_readiness_context(session_id="99f-readiness", checks=_passed_readiness_checks())
    lifecycle = get_lifecycle_session(session_id="99f-readiness")
    assert lifecycle is not None
    assert lifecycle.get("repo") == "pilotmain/aethos"
    assert is_readiness_only_lifecycle(lifecycle)
    assert lifecycle_plan_snapshot(lifecycle) is None
    plan_section = lifecycle.get("plan") or {}
    assert plan_section.get("exists") is False


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
def test_create_plan_uses_pre_plan_readiness_and_writes_plan_snapshot(
    mock_options,
    mock_readiness,
) -> None:
    mock_options.return_value = []
    mock_readiness.side_effect = AssertionError("should not rerun readiness when pre_plan lifecycle passed")
    save_lifecycle_record(session_id="99f-plan-orig", record=_readiness_only_lifecycle(session_id="99f-plan-orig"))
    _CONTEXT_STORE.clear()

    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="99f-plan-new",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_plan_draft"
    assert "readiness must pass" not in body.lower()

    plan = get_deployment_plan_context(session_id="99f-plan-new")
    assert plan is not None
    assert plan.get("repo") == "pilotmain/aethos"
    assert plan.get("stage") == "plan_draft"

    lifecycle = get_lifecycle_session(session_id="99f-plan-new")
    assert lifecycle is not None
    assert lifecycle_plan_snapshot(lifecycle) is not None
    assert (lifecycle.get("plan") or {}).get("exists") is True
    assert not is_readiness_only_lifecycle(lifecycle)


def test_simulator_on_pre_plan_gives_next_step_not_corrupt_error() -> None:
    save_lifecycle_record(session_id="99f-sim-orig", record=_readiness_only_lifecycle(session_id="99f-sim-orig"))
    _CONTEXT_STORE.clear()

    routed = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="99f-sim-new",
    )
    assert routed is not None
    body, intent, _meta = routed
    assert intent == "railway_service_creation_simulation_not_ready"
    assert "Railway readiness has passed, but no deployment plan has been created yet" in body
    assert "create railway deployment plan for pilotmain/aethos" in body
    assert "does not contain a deployment plan snapshot" not in body
    assert "corrupt" not in body.lower()


def test_show_lifecycle_marks_pre_plan_as_readiness_only() -> None:
    save_lifecycle_record(session_id="99f-show", record=_readiness_only_lifecycle(session_id="99f-show"))
    routed = route_railway_deployment_lifecycle_diagnostics(
        "show railway deployment lifecycle",
        session_id="99f-show-other",
    )
    assert routed is not None
    body, intent, _meta = routed
    assert intent == "railway_deployment_lifecycle_diagnostics"
    assert "readiness-only (not a deployment plan)" in body
    assert "materialization status: readiness_only" in body

    trace = trace_railway_deployment_lifecycle_resolution(session_id="99f-show-other", user_text="")
    report = format_lifecycle_diagnostics_report(trace)
    assert "readiness-only (not a deployment plan)" in report


def test_load_best_global_distinguishes_pre_plan_from_corrupt() -> None:
    save_lifecycle_record(session_id="99f-pre", record=_readiness_only_lifecycle(session_id="99f-pre"))
    record, diag = load_best_global_lifecycle_record()
    assert record is None
    assert diag.get("reason") == "readiness_only_no_plan"
    entries = inspect_all_global_lifecycle_entries()
    assert entries
    assert entries[0]["materialization_status"] == "readiness_only"

    corrupt = _readiness_only_lifecycle(session_id="99f-corrupt")
    corrupt["plan"] = {
        "exists": True,
        "mutation_ready": False,
        "review_confirmed": False,
        "snapshot": {},
    }
    clear_lifecycle()
    save_lifecycle_record(session_id="99f-corrupt", record=corrupt)
    record2, diag2 = load_best_global_lifecycle_record()
    assert record2 is None
    assert diag2.get("reason") == "plan_snapshot_missing"


def test_repair_does_not_claim_plan_recovery_for_readiness_only() -> None:
    save_lifecycle_record(session_id="99f-repair", record=_readiness_only_lifecycle(session_id="99f-repair"))
    result = repair_railway_deployment_lifecycle(session_id="99f-repair-target")
    assert result["ok"] is False
    assert result["reason"] == "readiness_only_no_plan"
    report = format_lifecycle_repair_report(result)
    assert "Repair cannot recover a plan" in report
    assert "create railway deployment plan" in report


def test_ensure_lane_does_not_repair_loop_on_readiness_only_index() -> None:
    save_lifecycle_record(session_id="99f-ensure", record=_readiness_only_lifecycle(session_id="99f-ensure"))
    _CONTEXT_STORE.clear()
    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id="99f-ensure-new",
        require_plan=True,
    )
    assert lane.plan is None
    assert lane.ensure_result == "miss"
    assert lane.materialization_failure.get("reason") != "plan_snapshot_missing"
    readiness = get_readiness_context(session_id="99f-ensure-new")
    assert readiness is not None
    assert readiness.get("checks")


def test_compose_no_plan_after_readiness_only_message() -> None:
    save_lifecycle_record(session_id="99f-compose", record=_readiness_only_lifecycle(session_id="99f-compose"))
    body = compose_no_plan_after_lifecycle_ensure(
        ensure_result="miss",
        session_id="99f-compose",
        for_simulator=True,
    )
    assert "Railway readiness has passed" in body
    assert "does not contain a deployment plan snapshot" not in body

    result = force_materialize_latest_global_lifecycle(session_id="99f-compose-target")
    assert result["ok"] is False
    assert result["reason"] == "readiness_only_no_plan"
