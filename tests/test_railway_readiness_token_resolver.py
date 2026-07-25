# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 92B — Railway readiness uses canonical credential resolver."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
    run_deployment_readiness_checks,
)
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
    compose_readiness_blocker,
    compose_readiness_report,
)
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_safe_runtime import (
    safe_route_railway_deployment_readiness,
)

_SECRET = "rw_secret_token_do_not_leak_abcdef1234567890"


@patch("aethos_core.providers.railway.api_client.test_connection")
@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
@patch("aethos_core.credentials.get_provider_api_token")
def test_readiness_token_passes_when_canonical_resolver_returns_token(
    mock_get_token,
    mock_inventory,
    mock_test_connection,
) -> None:
    mock_get_token.return_value = _SECRET
    mock_test_connection.return_value = {"ok": True, "detail": "ok", "account_email": "ops@example.com"}
    mock_inventory.return_value = type(
        "Inv",
        (),
        {"error": None, "freshness": "ok", "projects": []},
    )()

    checks = run_deployment_readiness_checks(user_text="run railway deployment readiness")
    assert checks["railway_credential_ok"] is True
    assert checks["railway_credential_source"] == "canonical provider credential resolver"

    report = compose_readiness_report(checks)
    assert "Railway token: **pass**" in report
    assert "Credential source: canonical provider credential resolver" in report
    assert _SECRET not in report

    blocker = compose_readiness_blocker(checks)
    assert "Railway token: **pass**" in blocker or checks["readonly_readiness_ok"]


@patch("aethos_core.credentials.get_provider_api_token", return_value=None)
def test_readiness_token_fails_when_resolver_returns_none(mock_get_token) -> None:
    checks = run_deployment_readiness_checks(user_text="run railway deployment readiness")
    assert checks["railway_credential_ok"] is False
    assert checks["railway_credential_source"] == "canonical provider credential resolver"
    mock_get_token.assert_called_with("railway")

    blocker = compose_readiness_blocker(checks)
    assert "Railway token: **fail**" in blocker
    assert "Checked source: canonical provider credential resolver" in blocker


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks")
def test_safe_route_never_logs_raw_token(mock_run) -> None:
    mock_run.return_value = {
        "readonly_readiness_ok": True,
        "railway_credential_ok": True,
        "railway_credential_source": "canonical provider credential resolver",
        "railway_api_connection_ok": True,
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": True, "project_count": 0, "environment_count": 0, "service_count": 0, "projects": []},
        "github_binding": {"github_credential_ok": True},
        "service_creation": {"governed_mutation_adapter_ops": ["restart", "redeploy"], "env_var_writes_enabled": False},
        "execution_mode": "api",
        "railway_credential_detail": _SECRET,
    }
    result = safe_route_railway_deployment_readiness("run railway deployment readiness", session_id="no-leak")
    assert result is not None
    body, _intent, meta = result
    assert _SECRET not in body
    assert _SECRET not in str(meta)
