# SPDX-License-Identifier: Apache-2.0
"""RAILWAY_GREENFIELD_DEPLOYMENT_FROM_LOCAL_WORKSPACE tests."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.connections.validation_status import VALIDATED
from aethos_core.execution_brain.execution_brain_router import route_execution_brain_turn
from aethos_core.provider_e2e_execution.railway_e2e_execution import route_railway_e2e_execution
from aethos_core.providers.railway.greenfield_deployment.greenfield_flow import run_railway_greenfield_deployment_flow
from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
    is_railway_greenfield_deployment_intent,
)
from aethos_core.providers.railway.greenfield_deployment.greenfield_router import (
    route_railway_greenfield_deployment_flow,
)
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests

_SECRET = "railway_greenfield_secret_token_1234567890"
_LIST_SERVICES_PATCH = "aethos_core.providers.railway.credential_truth.list_services_with_status"

GREENFIELD_PROMPT = (
    "AethOS is a new project. Check local workspace, get its remote git, "
    "create a new Railway project, deploy, set required env vars, and report back."
)


@pytest.fixture(autouse=True)
def _isolated_deployment_registry(tmp_path, monkeypatch):
    registry_dir = tmp_path / "deployment_targets"
    registry_dir.mkdir()
    monkeypatch.setenv("DEPLOYMENT_TARGETS_REGISTRY_DIR", str(registry_dir))
    from aethos_core.config import get_settings
    from aethos_core.deployment_targets.resolver import clear_session_deploy_targets_for_tests

    get_settings.cache_clear()
    clear_session_deploy_targets_for_tests()
    yield
    clear_session_deploy_targets_for_tests()
    get_settings.cache_clear()


@pytest.fixture
def vault_paths(tmp_path, monkeypatch):
    cred_dir = tmp_path / "credentials"
    monkeypatch.setenv("CREDENTIALS_DIR", str(cred_dir))
    monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    monkeypatch.setattr(settings, "railway_api_token", "")
    yield cred_dir
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


@pytest.fixture
def local_repo(tmp_path):
    repo = tmp_path / "AethOS"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname = 'aethos'\n", encoding="utf-8")
    (repo / ".env.example").write_text("ANTHROPIC_API_KEY=\nDATABASE_URL=\nPORT=8010\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "ops@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "AethOS Test"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:pilotmain/AethOS.git"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


def _store_validated(vault_paths) -> None:
    vault = CredentialVault(vault_paths)
    rec = vault.store_api_token(provider="railway", label="Railway primary", token=_SECRET)
    vault.mark_validation_result(rec.credential_id, status=VALIDATED, ok=True)
    reset_credential_vault_for_tests()
    CredentialVault(vault_paths)


def _inventory_ok(token, *args, **kwargs):
    _ = (token, args, kwargs)
    return {"ok": True, "services": [], "error": None}


def test_greenfield_intent_matches_user_prompt():
    assert is_railway_greenfield_deployment_intent(GREENFIELD_PROMPT)
    assert is_railway_greenfield_deployment_intent("deploy this local workspace to Railway")
    assert is_railway_greenfield_deployment_intent("create a new Railway project and deploy AethOS")
    assert not is_railway_greenfield_deployment_intent("redeploy the existing Railway api service")


def test_greenfield_does_not_route_to_existing_service_resolver(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: local_repo,
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        e2e = route_railway_e2e_execution(GREENFIELD_PROMPT, session_id="gf-e2e")
        brain = route_execution_brain_turn(GREENFIELD_PROMPT, session_id="gf-brain")

    assert e2e is None
    assert brain is None


def test_missing_local_workspace_blocker(tmp_path, vault_paths, monkeypatch):
    _store_validated(vault_paths)
    missing = tmp_path / "missing-workspace"
    monkeypatch.setattr(
        "aethos_core.local_workspace.portfolio.resolve_repo_reference",
        lambda *args, **kwargs: {"source": "none", "resolved_path": "", "path": ""},
    )
    monkeypatch.setattr(
        "aethos_core.local_workspace.portfolio.find_project_in_portfolio",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "aethos_core.local_workspace.registry.list_workspaces",
        lambda: [],
    )
    monkeypatch.setattr(
        "aethos_core.local_workspace.registry.find_workspace_by_hint",
        lambda hint: None,
    )
    monkeypatch.setattr(
        "aethos_core.production.deployment_mode.is_hosted_deployment",
        lambda: False,
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: missing,
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        result = run_railway_greenfield_deployment_flow(GREENFIELD_PROMPT, session_id="gf-no-ws")

    assert result.blocked is True
    assert result.blocker_code == "LOCAL_WORKSPACE_NOT_CONFIGURED"
    assert "Local Workspaces" in result.reply


def test_missing_git_remote_blocker(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    bare = local_repo / "bare"
    bare.mkdir()
    (bare / "aethos_core").mkdir()
    (bare / "tests").mkdir()
    (bare / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=bare, check=True, capture_output=True)
    monkeypatch.setattr(
        "aethos_core.local_workspace.portfolio.resolve_repo_reference",
        lambda *args, **kwargs: {"source": "none", "resolved_path": "", "path": ""},
    )
    monkeypatch.setattr(
        "aethos_core.local_workspace.portfolio.find_project_in_portfolio",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "aethos_core.local_workspace.registry.list_workspaces",
        lambda: [],
    )
    monkeypatch.setattr(
        "aethos_core.local_workspace.registry.find_workspace_by_hint",
        lambda hint: None,
    )
    monkeypatch.setattr(
        "aethos_core.production.deployment_mode.is_hosted_deployment",
        lambda: False,
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: bare,
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        result = run_railway_greenfield_deployment_flow(GREENFIELD_PROMPT, session_id="gf-no-git")

    assert result.blocked is True
    assert result.blocker_code == "GIT_REMOTE_MISSING"


def test_greenfield_flow_creates_preflight(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: local_repo,
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        result = run_railway_greenfield_deployment_flow(GREENFIELD_PROMPT, session_id="gf-preflight")

    assert result.ok is True
    assert result.preflight_job_id
    assert "greenfield" in result.reply.lower()
    assert "pilotmain/AethOS" in result.reply
    assert "ANTHROPIC_API_KEY" in result.reply
    assert _SECRET not in result.reply
    assert "TARGET_SERVICE_MISSING" not in result.reply


def test_env_names_without_values(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: local_repo,
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        result = run_railway_greenfield_deployment_flow(GREENFIELD_PROMPT, session_id="gf-env")

    env_report = result.artifacts.get("required_env_var_report") or {}
    assert "ANTHROPIC_API_KEY" in env_report.get("required_env_var_names", [])
    assert "secure_store://env/ANTHROPIC_API_KEY" in env_report.get("secure_references", [])
    assert "=" not in result.reply.split("ANTHROPIC_API_KEY")[1][:20]


def test_chat_routes_greenfield_not_brain(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: local_repo,
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        chat = resolve_chat_turn(GREENFIELD_PROMPT, session_id="gf-chat", apply_relational_layer=False)

    assert chat.intent == "railway_greenfield_deployment_preflight"
    assert "TARGET_SERVICE_MISSING" not in chat.reply
    assert "existing-service redeploy" in chat.reply.lower() or "new project" in chat.reply.lower()


def test_router_meta_includes_job(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: local_repo,
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        routed = route_railway_greenfield_deployment_flow(GREENFIELD_PROMPT, session_id="gf-meta")

    assert routed is not None
    _body, intent, meta = routed
    assert intent == "railway_greenfield_deployment_preflight"
    assert meta.get("preflight_created") == "true"
    assert meta.get("mutation_performed") == "false"
    assert meta.get("job_id")


@pytest.fixture
def hosted_env(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_hosted_deploy_uses_github_repo_not_local_workspace(hosted_env, monkeypatch):
    remote = {
        "ok": True,
        "repository": "pilotmain/killit",
        "branch": "main",
        "project_name": "killit",
        "owner": "pilotmain",
        "repo": "killit",
        "remote_url": "https://github.com/pilotmain/killit",
    }
    inspection = {
        "ok": True,
        "runtime": "Node",
        "required_env_var_names": ["PORT"],
        "build_command": "npm run build",
        "start_command": "npm start",
    }
    checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
    }

    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        lambda **kwargs: checks,
    )
    monkeypatch.setattr(
        "aethos_core.providers.vercel.greenfield_deployment.remote_repo_source.resolve_remote_github_repo_from_text",
        lambda *args, **kwargs: remote,
    )
    monkeypatch.setattr(
        "aethos_core.providers.vercel.greenfield_deployment.remote_repo_inspection.inspect_remote_github_repo_for_deployment",
        lambda **kwargs: inspection,
    )
    monkeypatch.setattr(
        "aethos_core.deployment_targets.resolver.resolve_workspace_hint_for_session",
        lambda *args, **kwargs: "killit",
    )
    monkeypatch.setattr(
        "aethos_core.deployment_targets.resolver.resolve_deployment_target",
        lambda *args, **kwargs: {"ok": True, "repo": "pilotmain/killit", "alias": "killit"},
    )

    with patch(
        "aethos_core.providers.railway.greenfield_deployment.greenfield_flow.create_railway_greenfield_preflight_job",
    ) as create_preflight:
        create_preflight.return_value = {
            "ok": True,
            "preflight_id": "rgf-test123",
            "job_id": "job-hostedgf01",
            "job_type": "railway_greenfield_deployment_preflight",
            "steps": [],
            "plan": {"repo": "pilotmain/killit", "service_name": "killit"},
        }
        with patch(
            "aethos_core.solo_execution.solo_greenfield_executor.maybe_run_solo_greenfield_execution",
            return_value=None,
        ):
            result = run_railway_greenfield_deployment_flow(
                "deploy killit to railway",
                session_id="web-session-test",
            )

    assert result.blocked is False
    assert result.preflight_job_id
    assert "LOCAL_WORKSPACE_NOT_CONFIGURED" not in result.blocker_code
    local_report = result.artifacts.get("local_workspace_deployment_source_report") or {}
    assert local_report.get("source") == "remote_github"
    assert (result.artifacts.get("git_remote_resolution_report") or {}).get("repository") == "pilotmain/killit"


def test_hosted_without_github_repo_blocks_without_local_workspace_prompt(hosted_env, monkeypatch):
    checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
    }
    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        lambda **kwargs: checks,
    )
    monkeypatch.setattr(
        "aethos_core.providers.vercel.greenfield_deployment.remote_repo_source.resolve_remote_github_repo_from_text",
        lambda *args, **kwargs: {
            "ok": False,
            "blocker_code": "REMOTE_REPO_NOT_FOUND",
            "detail": "GitHub repo `killit` not accessible.",
        },
    )
    monkeypatch.setattr(
        "aethos_core.deployment_targets.resolver.resolve_workspace_hint_for_session",
        lambda *args, **kwargs: "killit",
    )
    monkeypatch.setattr(
        "aethos_core.deployment_targets.resolver.resolve_deployment_target",
        lambda *args, **kwargs: {"ok": False, "blocker_code": "REMOTE_REPO_MISSING"},
    )

    result = run_railway_greenfield_deployment_flow("deploy killit to railway", session_id="web-session-test")

    assert result.blocked is True
    assert result.blocker_code != "LOCAL_WORKSPACE_NOT_CONFIGURED"
    assert "local workspace" not in result.reply.lower()
