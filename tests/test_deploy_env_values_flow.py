# SPDX-License-Identifier: Apache-2.0
"""Deploy env values flow — resolution, guidance, and turn-finalize helpers."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.providers.railway.env_value_readiness.deployment_env_guidance import (
    assess_deployment_env_for_plan,
    compose_deployment_env_block_report,
)
from aethos_core.providers.railway.env_value_readiness.deployment_env_store import (
    clear_deployment_env_store_for_tests,
    register_deployment_env_value,
)
from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import (
    resolve_env_var_from_secure_store,
)
from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
    clear_deployment_env_presence_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_deployment_env_store_for_tests()
    clear_deployment_env_presence_for_tests()
    yield
    clear_deployment_env_store_for_tests()
    clear_deployment_env_presence_for_tests()


def _plan() -> dict:
    return {
        "repo": "pilotmain/killit",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "killit-api",
    }


@patch("aethos_core.credentials.get_provider_api_token")
def test_anthropic_auto_resolves_from_connections(mock_token) -> None:
    mock_token.return_value = "sk-ant-test-key"
    resolved = resolve_env_var_from_secure_store("ANTHROPIC_API_KEY", plan=_plan())
    assert resolved.ok is True
    assert resolved.source == "credential_center"
    mock_token.assert_called()


def test_deployment_store_value_resolves_without_presence_flag() -> None:
    target_key = "pilotmain/killit|pilotos|staging|killit-api"
    register_deployment_env_value(
        target_key=target_key,
        name="CRON_SECRET",
        value="cron-secret-value",
    )
    resolved = resolve_env_var_from_secure_store("CRON_SECRET", plan=_plan())
    assert resolved.ok is True
    assert resolved.source == "secure_store_reference"


@patch("aethos_core.credentials.get_provider_api_token")
def test_deploy_env_values_blocked_report_lists_missing_with_guidance(mock_token) -> None:
    def _token(provider: str, *, require_validated: bool = True) -> str | None:
        return "sk-ant-test" if provider == "anthropic" else None

    mock_token.side_effect = _token
    env_report = {
        "required_env_var_names": ["ANTHROPIC_API_KEY", "CRON_SECRET", "STRIPE_SECRET_KEY"],
        "env_var_hints": {"CRON_SECRET": "Auth for scheduled jobs"},
    }
    assessment = assess_deployment_env_for_plan(plan=_plan(), env_report=env_report)
    assert "ANTHROPIC_API_KEY" in assessment.resolved_names
    assert "CRON_SECRET" in assessment.missing_names
    assert "STRIPE_SECRET_KEY" in assessment.missing_names
    summary, full = compose_deployment_env_block_report(assessment)
    assert "Deploy blocked" in summary
    assert "Deployment env values" in full
    assert "CRON_SECRET" in full
    assert "Auth for scheduled jobs" in full


@patch("aethos_core.credentials.get_provider_api_token", return_value=None)
def test_after_values_stored_deploy_resolves_missing(mock_token) -> None:
    env_report = {"required_env_var_names": ["CRON_SECRET", "STRIPE_SECRET_KEY"]}
    assessment_before = assess_deployment_env_for_plan(plan=_plan(), env_report=env_report)
    assert "CRON_SECRET" in assessment_before.missing_names
    assert "STRIPE_SECRET_KEY" in assessment_before.missing_names

    target_key = assessment_before.target_key
    register_deployment_env_value(target_key=target_key, name="CRON_SECRET", value="cron-v")
    register_deployment_env_value(target_key=target_key, name="STRIPE_SECRET_KEY", value="sk_test")

    assessment_after = assess_deployment_env_for_plan(plan=_plan(), env_report=env_report)
    assert "CRON_SECRET" not in assessment_after.missing_names
    assert "STRIPE_SECRET_KEY" not in assessment_after.missing_names
