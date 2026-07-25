# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 100A — readiness-only lifecycle must not block plan creation."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
    _lifecycle_stage,
    is_readiness_only_lifecycle,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
    lifecycle_plan_snapshot,
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
    save_readiness_context,
)
from tests.test_railway_pre_plan_lifecycle_behavior import (
    _passed_readiness_checks,
    _readiness_only_lifecycle,
)


def setup_function() -> None:
    clear_plan()
    clear_readiness()
    clear_lifecycle()


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
def test_readiness_only_lifecycle_allows_plan_creation(mock_options, mock_readiness) -> None:
    mock_options.return_value = []
    mock_readiness.side_effect = AssertionError("readiness must not rerun")
    record = _readiness_only_lifecycle(session_id="100a-orig")
    save_lifecycle_record(session_id="100a-orig", record=record)
    _CONTEXT_STORE.clear()

    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="100a-new",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_plan_draft"
    assert "readiness must pass" not in body.lower()
    assert "Railway deployment readiness must pass" not in body

    plan = get_deployment_plan_context(session_id="100a-new")
    assert plan is not None
    assert plan.get("stage") == "plan_draft"
    assert lifecycle_plan_snapshot(get_lifecycle_session(session_id="100a-new")) is not None


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
def test_empty_lifecycle_checks_still_allows_plan(mock_options, mock_readiness) -> None:
    """Regression: passed readiness with empty checks dict must not loop."""
    mock_options.return_value = []
    mock_readiness.side_effect = AssertionError("readiness must not rerun")
    record = _readiness_only_lifecycle(session_id="100a-empty")
    record["readiness"]["checks"] = {}
    save_lifecycle_record(session_id="100a-empty", record=record)
    _CONTEXT_STORE.clear()

    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="100a-empty-new",
    )
    assert result is not None
    assert result[1] == "railway_deployment_plan_draft"
    mock_readiness.assert_not_called()


@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
def test_readiness_store_only_session_lifecycle(mock_options) -> None:
    mock_options.return_value = []
    save_readiness_context(session_id="100a-store", checks=_passed_readiness_checks())
    lifecycle = get_lifecycle_session(session_id="100a-store")
    assert is_readiness_only_lifecycle(lifecycle)
    assert _lifecycle_stage(lifecycle) in {"pre_plan", "readiness_passed"}

    result = route_railway_new_service_plan(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="100a-store",
    )
    assert result is not None
    assert result[1] == "railway_deployment_plan_draft"
    updated = get_lifecycle_session(session_id="100a-store")
    assert updated is not None
    assert (updated.get("plan") or {}).get("exists") is True
    assert _lifecycle_stage(updated) in {"plan_unconfirmed", "plan_confirmed", "preflight_ready", "simulated"}
