# SPDX-License-Identifier: Apache-2.0
"""Tests for deployment env filtering and greenfield deploy intent."""

from __future__ import annotations

from aethos_core.providers.railway.env_value_readiness.env_deployment_filter import (
    filter_greenfield_deployment_env_var_names,
)
from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
    is_railway_greenfield_deployment_intent,
)
from aethos_core.solo_execution.solo_execution_mode import validate_solo_greenfield_eligibility


def test_deploy_to_railway_with_env_and_verify_is_greenfield():
    assert is_railway_greenfield_deployment_intent(
        "Deploy AethOS to Railway with env vars and verify it."
    )


def test_filter_excludes_host_config_from_env_example_keys():
    names = filter_greenfield_deployment_env_var_names(
        [
            "ANTHROPIC_API_KEY",
            "APP_ENV",
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED",
            "SOFTWARE_DELIVERY_PHASE_2_FROZEN",
            "LOCAL_WORKSPACE_REGISTRY_DIR",
        ],
        plan={"environment": "staging", "repo": "pilotmain/AethOS"},
    )
    assert "ANTHROPIC_API_KEY" in names
    assert "WEB_SEARCH_API_KEY" in names
    assert "RAILWAY_GREENFIELD_EXECUTION_ENABLED" not in names
    assert "SOFTWARE_DELIVERY_PHASE_2_FROZEN" not in names
    assert "LOCAL_WORKSPACE_REGISTRY_DIR" not in names
    assert "APP_ENV" not in names


def test_solo_eligibility_accepts_local_env_secrets(monkeypatch):
    monkeypatch.setenv("AETHOS_SOLO_EXECUTION_MODE", "true")
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-local-secret")
    monkeypatch.setenv("WEB_SEARCH_API_KEY", "test-search-secret")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    result = validate_solo_greenfield_eligibility(
        plan={"repo": "pilotmain/AethOS", "environment": "staging", "project": "pilotos", "service_name": "aethos-api"},
        env_report={"required_env_var_names": ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"]},
        git_remote={"repository": "pilotmain/AethOS"},
        provider="railway",
    )
    get_settings.cache_clear()
    assert result.ok is True
