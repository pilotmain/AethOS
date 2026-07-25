# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 104C — staging/dry_run readiness-only lifecycle must match simulator and plan router."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
    has_passed_readiness_without_plan,
    is_corrupt_plan_lifecycle,
    normalize_lifecycle_for_plan_creation,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
    resolve_readiness_for_plan_creation,
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
)
from aethos_core.providers.railway.service_creation_simulator.simulator_lifecycle_snapshots import (
    lifecycle_readiness_status_passed,
    load_readiness_checks_snapshot,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)
from tests.test_railway_pre_plan_lifecycle_behavior import (
    _passed_readiness_checks,
    _readiness_only_lifecycle,
)


def setup_function() -> None:
    clear_plan()
    clear_readiness()
    clear_lifecycle()


def _corrupt_plan_flags(record: dict) -> dict:
    record = dict(record)
    record["plan"] = {
        "exists": True,
        "mutation_ready": False,
        "review_confirmed": False,
        "snapshot": {},
    }
    return record


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
def test_staging_readiness_only_lifecycle_allows_plan_creation(mock_options, mock_readiness) -> None:
    mock_options.return_value = []
    mock_readiness.side_effect = AssertionError("readiness must not rerun for staging")
    save_lifecycle_record(session_id="104c-staging", record=_readiness_only_lifecycle(session_id="104c-staging"))
    _CONTEXT_STORE.clear()

    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / staging",
        session_id="104c-staging",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_plan_draft"
    assert "readiness must pass" not in body.lower()
    assert "Railway deployment readiness must pass" not in body
    mock_readiness.assert_not_called()

    plan = get_deployment_plan_context(session_id="104c-staging")
    assert plan is not None
    assert str(plan.get("environment") or "").lower() == "staging"


@patch(
    "aethos_core.providers.railway.execution_contract.execution_enablement.load_railway_execution_enablement_config"
)
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
def test_dry_run_staging_corrupt_plan_flags_still_allow_plan(
    mock_options,
    mock_readiness,
    mock_enablement,
) -> None:
    mock_options.return_value = []
    mock_readiness.side_effect = AssertionError("readiness must not rerun in dry_run staging")
    mock_enablement.return_value = type("Cfg", (), {"mode": "dry_run"})()

    record = _corrupt_plan_flags(_readiness_only_lifecycle(session_id="104c-dry"))
    assert is_corrupt_plan_lifecycle(record)
    save_lifecycle_record(session_id="104c-dry", record=record)
    _CONTEXT_STORE.clear()

    resolution = resolve_readiness_for_plan_creation(
        session_id="104c-dry",
        user_text="create railway deployment plan for pilotmain/aethos in pilotos / staging",
    )
    assert resolution.satisfied
    assert resolution.readiness_only
    assert resolution.execution_mode == "dry_run"

    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / staging",
        session_id="104c-dry",
    )
    assert result is not None
    assert result[1] == "railway_deployment_plan_draft"
    mock_readiness.assert_not_called()


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_simulator_and_plan_router_agree_on_staging_readiness(mock_readiness) -> None:
    mock_readiness.side_effect = AssertionError("readiness must not rerun")
    save_lifecycle_record(session_id="104c-agree", record=_readiness_only_lifecycle(session_id="104c-agree"))
    _CONTEXT_STORE.clear()

    assert lifecycle_readiness_status_passed(session_id="104c-agree")
    checks = load_readiness_checks_snapshot(session_id="104c-agree")
    assert checks is not None
    assert checks.get("readonly_readiness_ok") is True

    sim = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="104c-agree",
    )
    assert sim is not None
    sim_body = sim[0].lower()
    assert "readiness has passed" in sim_body or "no deployment plan" in sim_body

    with patch(
        "aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options",
        return_value=[],
    ):
        plan = route_railway_new_service_plan(
            "create railway deployment plan for pilotmain/aethos in pilotos / staging",
            session_id="104c-agree",
        )
    assert plan is not None
    assert plan[1] == "railway_deployment_plan_draft"
    assert "readiness must pass" not in plan[0].lower()


def test_normalize_clears_corrupt_plan_for_readiness_only() -> None:
    record = _corrupt_plan_flags(_readiness_only_lifecycle(session_id="104c-norm"))
    normalized = normalize_lifecycle_for_plan_creation(record)
    assert normalized is not None
    assert not is_corrupt_plan_lifecycle(normalized)
    assert has_passed_readiness_without_plan(normalized)


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
def test_merged_corrupt_plan_from_legacy_merge_allows_plan(mock_options, mock_readiness) -> None:
    """Regression: merged lifecycle with plan.exists=True but empty snapshot blocked plan router."""
    mock_options.return_value = []
    mock_readiness.side_effect = AssertionError("readiness must not rerun after merge normalize")
    record = _corrupt_plan_flags(_readiness_only_lifecycle(session_id="104c-merge-src"))
    save_lifecycle_record(session_id="104c-merge-src", record=record)

    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / staging",
        session_id="104c-merge-new",
    )
    assert result is not None
    assert result[1] == "railway_deployment_plan_draft"
    mock_readiness.assert_not_called()
    lifecycle = get_lifecycle_session(session_id="104c-merge-new")
    assert lifecycle is not None
    assert (lifecycle.get("plan") or {}).get("exists") is True
