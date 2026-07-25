# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 92C — Railway readiness status wording."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
    compose_readiness_blocker,
    compose_readiness_passed_not_mutation_ready,
    readonly_checks_passed,
)
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_router import (
    route_railway_deployment_readiness,
)
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_safe_runtime import (
    safe_route_railway_deployment_readiness,
)


def _all_pass_checks() -> dict:
    return {
        "readonly_readiness_ok": True,
        "mutation_ready": False,
        "railway_credential_ok": True,
        "railway_credential_source": "canonical provider credential resolver",
        "railway_api_connection_ok": True,
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "referenced_github_repo": "pilotmain/aethos",
        "inventory": {"ok": True, "project_count": 1, "environment_count": 1, "service_count": 1, "projects": []},
        "github_binding": {"github_credential_ok": True, "accessible_repos_count": 1},
        "service_creation": {
            "graphql_service_create": False,
            "governed_mutation_adapter_ops": ["restart", "redeploy"],
            "env_var_writes_enabled": False,
        },
        "execution_mode": "api",
    }


def test_all_checks_pass_mutation_unavailable_uses_passed_intent() -> None:
    checks = _all_pass_checks()
    assert readonly_checks_passed(checks)
    result = route_railway_deployment_readiness("run railway deployment readiness", session_id="wording-92c")
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_deployment_readiness_passed_not_mutation_ready"
    assert meta.get("readonly_readiness_ok") == "true"
    assert meta.get("mutation_ready") == "false"
    assert "checks passed" in body.lower()
    assert "one readonly check failed" not in body.lower()
    assert "Greenfield Railway service creation is not wired" in body
    assert "Credential source: canonical provider credential resolver" in body


def test_compose_passed_not_mutation_ready_shape() -> None:
    body = compose_readiness_passed_not_mutation_ready(_all_pass_checks())
    assert "Railway deployment readiness checks passed." in body
    assert "Railway token: **pass**" in body
    assert "one readonly check failed" not in body
    assert "No service has been created." in body


def test_failed_readonly_check_still_uses_blocked_wording() -> None:
    checks = _all_pass_checks()
    checks["railway_credential_ok"] = False
    checks["readonly_readiness_ok"] = False
    body = compose_readiness_blocker(checks)
    assert "one readonly check failed" in body
    assert "Railway token: **fail**" in body
    assert "checks passed" not in body.lower()


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks")
def test_safe_route_passed_not_blocked_when_all_readonly_ok(mock_run) -> None:
    mock_run.return_value = _all_pass_checks()
    result = safe_route_railway_deployment_readiness(
        "run railway deployment readiness for pilotmain/aethos",
        session_id="safe-wording",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_readiness_passed_not_mutation_ready"
    assert "one readonly check failed" not in body.lower()
