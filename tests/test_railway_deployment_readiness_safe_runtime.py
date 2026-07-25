# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 91B — Railway deployment readiness crash isolation."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
    extract_github_repo_target,
    safe_run_deployment_readiness_checks,
)
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import clear_for_tests
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_safe_runtime import (
    safe_route_railway_deployment_readiness,
)
from aethos_core.chat.service import resolve_chat_turn


def setup_function() -> None:
    clear_for_tests()


def test_extract_github_repo_target_for_phrase() -> None:
    assert extract_github_repo_target("run railway deployment readiness for pilotmain/aethos") == "pilotmain/aethos"
    assert extract_github_repo_target("readiness from pilotmain/aethos") == "pilotmain/aethos"


def test_extract_does_not_treat_slash_as_url_path() -> None:
    repo = extract_github_repo_target("run railway deployment readiness for pilotmain/aethos")
    assert repo == "pilotmain/aethos"
    assert repo != "pilotmain"
    assert "/aethos" not in repo.split("/")[0]


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks")
def test_readiness_for_repo_never_crashes(mock_run) -> None:
    mock_run.side_effect = AttributeError("'str' object has no attribute 'full_name'")
    result = safe_route_railway_deployment_readiness(
        "run railway deployment readiness for pilotmain/aethos",
        session_id="safe-91b",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_deployment_readiness_blocked"
    assert "internal error" not in body.lower()
    assert "one readonly check failed" in body.lower()
    assert "No mutation has been performed." in body
    assert meta.get("referenced_github_repo") == "pilotmain/aethos" or "pilotmain/aethos" in body


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks")
def test_failed_inventory_returns_blocker(mock_run) -> None:
    mock_run.return_value = {
        "readonly_readiness_ok": False,
        "referenced_github_repo": "pilotmain/aethos",
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "railway_credential_detail": "ok",
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": False, "error": "GraphQL discovery failed"},
        "github_binding": {"github_credential_ok": True, "accessible_repos_count": 1},
        "service_creation": {"graphql_service_create": False},
    }
    result = safe_route_railway_deployment_readiness(
        "run railway deployment readiness for pilotmain/aethos",
        session_id="inv-fail",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_readiness_blocked"
    assert "Railway inventory: **fail**" in body
    assert "pilotmain/aethos" in body


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks")
def test_missing_railway_token_returns_blocker(mock_run) -> None:
    mock_run.return_value = {
        "readonly_readiness_ok": False,
        "referenced_github_repo": "pilotmain/aethos",
        "railway_credential_ok": False,
        "railway_api_connection_ok": False,
        "railway_credential_detail": "missing Railway API token",
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": False, "error": "no token"},
        "github_binding": {"github_credential_ok": False, "accessible_repos_count": 0},
        "service_creation": {},
    }
    result = safe_route_railway_deployment_readiness(
        "run railway deployment readiness for pilotmain/aethos",
        session_id="no-token",
    )
    assert result is not None
    body, intent, _meta = result
    assert intent == "railway_deployment_readiness_blocked"
    assert "Railway token: **fail**" in body
    assert "missing Railway API token" in body or "Diagnostic" in body


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks")
def test_resolve_chat_turn_never_cognition_crash(mock_checks) -> None:
    mock_checks.return_value = {
        "readonly_readiness_ok": True,
        "referenced_github_repo": "pilotmain/aethos",
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": True, "project_count": 1, "environment_count": 1, "service_count": 1, "projects": []},
        "github_binding": {"github_credential_ok": True, "accessible_repos_count": 1},
        "service_creation": {
            "governed_mutation_adapter_ops": ["restart", "redeploy"],
            "env_var_writes_enabled": False,
            "graphql_service_create_detail": "not wired",
        },
        "execution_mode": "api",
        "railway_credential_source": "env",
    }
    result = resolve_chat_turn(
        "run railway deployment readiness for pilotmain/aethos",
        session_id="chat-safe",
        apply_relational_layer=False,
    )
    assert result.intent in {
        "railway_deployment_readiness",
        "railway_deployment_readiness_blocked",
        "provider_e2e_readiness_report",
    }
    assert "internal error" not in (result.reply or "").lower()
    if result.intent in {"railway_deployment_readiness", "railway_deployment_readiness_blocked"}:
        assert "pilotmain/aethos" in result.reply


def test_safe_run_checks_never_raises() -> None:
    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks",
        side_effect=RuntimeError("boom"),
    ):
        checks = safe_run_deployment_readiness_checks(
            user_text="run railway deployment readiness for pilotmain/aethos",
            session_id="safe-run",
        )
    assert checks["readonly_readiness_ok"] is False
    assert checks.get("referenced_github_repo") == "pilotmain/aethos"
