# SPDX-License-Identifier: Apache-2.0
"""Railway Mission Control UI greenfield deploy routing."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.connections.validation_status import VALIDATED
from aethos_core.execution_brain.execution_brain_router import route_execution_brain_turn
from aethos_core.provider_e2e_execution.railway_e2e_execution import route_railway_e2e_execution
from aethos_core.providers.railway.greenfield_deployment.greenfield_deploy_component import (
    detect_greenfield_deploy_component,
    infer_greenfield_service_name,
)
from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
    is_railway_greenfield_deployment_intent,
)
from aethos_core.providers.railway.greenfield_deployment.target_plan import build_railway_greenfield_target_plan
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests

_SECRET = "railway_ui_deploy_token_1234567890"
_LIST_SERVICES_PATCH = "aethos_core.providers.railway.credential_truth.list_services_with_status"

UI_DEPLOY_PROMPT = "Deploy AethOS mission control UI to Railway in pilotos staging"
UI_FOLLOWUP_PROMPT = (
    "no im asking a new deployment for aethos mission control UI in railway, "
    "we already deployed aethos backend in pilotos now deploy aethos mission control UI"
)


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
    web = repo / "web"
    web.mkdir()
    (web / "package.json").write_text(
        '{"name":"aethos-web","scripts":{"build":"next build","start":"next start"}}',
        encoding="utf-8",
    )
    (web / ".env.local").write_text("NEXT_PUBLIC_API_BASE=https://aethos-api-staging.up.railway.app\n", encoding="utf-8")
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


def _patch_workspace(monkeypatch, local_repo):
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: local_repo,
    )


def test_ui_deploy_prompt_matches_greenfield_intent():
    assert is_railway_greenfield_deployment_intent(UI_DEPLOY_PROMPT)
    assert is_railway_greenfield_deployment_intent(UI_FOLLOWUP_PROMPT)


def test_ui_component_plan_uses_aethos_ui_service(local_repo):
    from aethos_core.providers.railway.greenfield_deployment.greenfield_deploy_component import inspect_component_repo

    component = detect_greenfield_deploy_component(UI_DEPLOY_PROMPT)
    assert component == "ui"
    assert infer_greenfield_service_name(text=UI_DEPLOY_PROMPT, repo="pilotmain/aethos", component=component) == "aethos-ui"
    inspection = inspect_component_repo(str(local_repo), component=component)
    plan = build_railway_greenfield_target_plan(
        user_text=UI_DEPLOY_PROMPT,
        git_remote={"repository": "pilotmain/aethos", "branch": "main", "remote_url": ""},
        local_source={"workspace_root": str(local_repo), "workspace_name": "AethOS"},
        local_inspection=inspection,
    )
    assert plan["service_name"] == "aethos-ui"
    assert plan["root_directory"] == "web"
    assert plan["deploy_component"] == "ui"
    assert plan["required_env_var_names"] == ["NEXT_PUBLIC_API_BASE"]


def test_ui_deploy_routes_greenfield_not_e2e(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    _patch_workspace(monkeypatch, local_repo)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        assert route_railway_e2e_execution(UI_FOLLOWUP_PROMPT, session_id="ui-no-e2e") is None
        assert route_execution_brain_turn(UI_FOLLOWUP_PROMPT, session_id="ui-no-brain") is None
        chat = resolve_chat_turn(UI_FOLLOWUP_PROMPT, session_id="ui-route", apply_relational_layer=False)

    assert chat.meta.get("route_id") == "railway_greenfield_deployment_flow"
    assert "TARGET_SERVICE_MISSING" not in chat.reply
    assert "aethos-ui" in chat.reply or chat.intent.startswith("railway_greenfield")


def test_can_also_deploy_ui_phrase(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    _patch_workspace(monkeypatch, local_repo)
    prompt = "can you also deploy aethos ui to railway"
    assert is_railway_greenfield_deployment_intent(prompt)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        chat = resolve_chat_turn(prompt, session_id="ui-also", apply_relational_layer=False)
    assert chat.meta.get("route_id") == "railway_greenfield_deployment_flow"
