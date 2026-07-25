# SPDX-License-Identifier: Apache-2.0
"""FIX 107 — secure env value presence UX."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests as clear_plan,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.env_value_readiness.env_minimum_secret_sets import (
    minimum_secrets_for_profile,
)
from aethos_core.providers.railway.env_value_readiness.env_presence_confidence import (
    EnvPresenceConfidence,
)
from aethos_core.providers.railway.env_value_readiness.env_rotation_metadata import (
    set_rotation_metadata_for_tests,
)
from aethos_core.providers.railway.env_value_readiness.env_value_context import (
    clear_for_tests as clear_env_ctx,
)
from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
    build_target_key,
    clear_deployment_env_presence_for_tests,
    set_deployment_env_presence_for_tests,
)
from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
    assess_env_value_readiness,
    compute_env_readiness_score,
)
from aethos_core.providers.railway.env_value_readiness.env_value_router import (
    route_railway_env_value_readiness,
)
from aethos_core.providers.railway.execution_contract.execution_readiness_gate import (
    evaluate_railway_execution_readiness,
)


def setup_function() -> None:
    clear_plan()
    clear_env_ctx()
    clear_deployment_env_presence_for_tests()
    get_settings.cache_clear()


def _plan(*, environment: str = "staging", env_names: list[str] | None = None) -> dict:
    return apply_plan_review_confirmation(
        {
            "plan_id": "plan-107",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": environment,
            "service_name": "aethos-api",
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": env_names
            or [
                "APP_ENV",
                "API_PORT",
                "ANTHROPIC_API_KEY",
                "WEB_SEARCH_API_KEY",
                "TELEGRAM_BOT_TOKEN",
                "TRIGGER_WEBHOOK_SECRET",
                "LOCAL_WORKSPACE_ARTIFACTS_DIR",
            ],
            "mutation_ready": True,
        }
    )


@patch("aethos_core.credentials.get_provider_api_token")
def test_staging_minimum_secret_set(mock_token, monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "dry_run")
    get_settings.cache_clear()
    plan = _plan(environment="staging")
    mock_token.return_value = "token-present"
    key = build_target_key(
        repo=plan["repo"],
        project=plan["project"],
        environment=plan["environment"],
        service_name=plan["service_name"],
    )
    set_deployment_env_presence_for_tests(
        target_key=key,
        present_names=["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
    )
    with patch.dict(os.environ, {}, clear=True):
        state = assess_env_value_readiness(plan=plan)
    assert state["minimum_secret_set_complete"] is True
    assert "TRIGGER_WEBHOOK_SECRET" not in state["critical_blockers"]
    assert "TELEGRAM_BOT_TOKEN" in state["optional_missing"] or "TELEGRAM_BOT_TOKEN" in state[
        "observability_warnings"
    ]


@patch("aethos_core.credentials.get_provider_api_token")
def test_production_minimum_includes_webhook_secrets(mock_token, monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
    get_settings.cache_clear()
    plan = _plan(environment="production")
    mock_token.return_value = None
    with patch.dict(os.environ, {}, clear=True):
        state = assess_env_value_readiness(plan=plan)
    minimum = list(minimum_secrets_for_profile("railway_production"))
    assert "TRIGGER_WEBHOOK_SECRET" in minimum
    assert "WEB_API_TOKEN" in minimum
    assert "TRIGGER_WEBHOOK_SECRET" in state["critical_blockers"]


@patch("aethos_core.credentials.get_provider_api_token")
def test_optional_integrations_do_not_block_dry_run(mock_token, monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "dry_run")
    get_settings.cache_clear()
    plan = _plan(environment="staging")
    key = build_target_key(
        repo=plan["repo"],
        project=plan["project"],
        environment=plan["environment"],
        service_name=plan["service_name"],
    )
    set_deployment_env_presence_for_tests(
        target_key=key,
        present_names=["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
    )
    mock_token.return_value = None
    with patch.dict(os.environ, {}, clear=True):
        state = assess_env_value_readiness(plan=plan)
    assert state["ready_for_dry_run"] is True
    assert "TELEGRAM_BOT_TOKEN" not in state["critical_blockers"]


def test_defaults_classified_without_values_in_report() -> None:
    plan = _plan(env_names=["APP_ENV", "API_PORT"])
    save_deployment_plan_context(session_id="107-defaults", plan=plan)
    state = assess_env_value_readiness(plan=plan)
    assert "APP_ENV" in state["using_default_names"]
    body = route_railway_env_value_readiness(
        "check railway env value readiness",
        session_id="107-defaults",
    )
    assert body is not None
    assert "APP_ENV=" not in body[0]
    assert "Using defaults:" in body[0]


@patch("aethos_core.credentials.get_provider_api_token", return_value="secret-token")
def test_source_attribution_without_value_leak(mock_token) -> None:
    save_deployment_plan_context(session_id="107-src", plan=_plan())
    result = route_railway_env_value_readiness(
        "show secure railway env readiness",
        session_id="107-src",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_env_value_readiness_secure_summary"
    assert meta["route_id"] == "railway_env_value_readiness"
    assert "credential_center" in body or "secure_store_reference" in body
    assert "secret-token" not in body
    assert "No secret values displayed" in body


def test_stale_metadata_rendering() -> None:
    plan = _plan()
    key = build_target_key(
        repo=plan["repo"],
        project=plan["project"],
        environment=plan["environment"],
        service_name=plan["service_name"],
    )
    set_rotation_metadata_for_tests(
        target_key=key,
        env_vars={"ANTHROPIC_API_KEY": {"rotation_state": "aging", "last_updated_days": 45}},
    )
    set_deployment_env_presence_for_tests(target_key=key, present_names=["ANTHROPIC_API_KEY"])
    with patch("aethos_core.credentials.get_provider_api_token", return_value="tok"):
        state = assess_env_value_readiness(plan=plan)
    entry = state["values"]["ANTHROPIC_API_KEY"]
    assert entry["confidence"] == EnvPresenceConfidence.STALE.value
    result = route_railway_env_value_readiness(
        "show secure railway env readiness",
        session_id="107-stale",
    )
    assert result is not None
    assert "rotation_state" in result[0]
    assert "tok" not in result[0]


def test_readiness_scoring() -> None:
    plan = _plan(env_names=["APP_ENV", "API_PORT"])
    state = assess_env_value_readiness(plan=plan)
    score = compute_env_readiness_score(state=state)
    assert 0 <= score <= 100
    assert state["env_readiness_confidence"] in {"high", "medium", "low"}


def test_compact_summary_rendering() -> None:
    save_deployment_plan_context(session_id="107-compact", plan=_plan())
    result = route_railway_env_value_readiness(
        "check railway env value readiness",
        session_id="107-compact",
    )
    assert result is not None
    body, _intent, meta = result
    assert "Critical blockers:" in body
    assert "Summary:" in body
    assert meta.get("env_profile") == "railway_staging"
    assert "minimum_secret_set_complete" in meta


def test_minimum_secrets_prompt() -> None:
    save_deployment_plan_context(session_id="107-min", plan=_plan())
    result = route_railway_env_value_readiness(
        "what minimum secrets are required?",
        session_id="107-min",
    )
    assert result is not None
    assert result[1] == "railway_env_value_readiness_minimum_secrets"
    assert "ANTHROPIC_API_KEY" in result[0]
    assert "WEB_SEARCH_API_KEY" in result[0]
    assert "Required only for production" in result[0]


@patch("aethos_core.credentials.get_provider_api_token")
def test_execution_gate_dry_run_uses_minimum_set(mock_token, monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "dry_run")
    get_settings.cache_clear()
    plan = _plan(environment="staging")
    key = build_target_key(
        repo=plan["repo"],
        project=plan["project"],
        environment=plan["environment"],
        service_name=plan["service_name"],
    )
    set_deployment_env_presence_for_tests(
        target_key=key,
        present_names=["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
    )
    mock_token.return_value = None
    gate = evaluate_railway_execution_readiness(
        "check railway execution readiness",
        plan=plan,
        preflight={"preflight_id": "pf-107", "preflight_approved": True},
        simulation={"simulation_id": "sim-107", "ready_to_execute": True},
    )
    matrix = gate.display_gate_matrix()
    assert matrix.get("minimum_secret_set_complete") == "complete"
    assert matrix.get("env_readiness_confidence") in {"high", "medium", "low"}
