# SPDX-License-Identifier: Apache-2.0
"""Tests for deployment target registry and resolver."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def isolated_deployment_registry(tmp_path: Path, monkeypatch):
    registry_dir = tmp_path / "deployment_targets"
    registry_dir.mkdir()
    monkeypatch.setenv("DEPLOYMENT_TARGETS_REGISTRY_DIR", str(registry_dir))
    from aethos_core.config import get_settings
    from aethos_core.deployment_targets.resolver import clear_session_deploy_targets_for_tests

    get_settings.cache_clear()
    clear_session_deploy_targets_for_tests()
    yield registry_dir
    clear_session_deploy_targets_for_tests()
    get_settings.cache_clear()


def test_register_and_resolve_by_alias(isolated_deployment_registry) -> None:
    from aethos_core.deployment_targets.registry import register_target
    from aethos_core.deployment_targets.resolver import resolve_deployment_target

    register_target(alias="killit", repo="pilotmain/killit", vercel_project="killit")

    with patch(
        "aethos_core.providers.vercel.greenfield_deployment.remote_repo_source._lookup_github_repo",
        return_value={"ok": True, "default_branch": "main", "html_url": "https://github.com/pilotmain/killit"},
    ):
        resolved = resolve_deployment_target("deploy killit to vercel fresh", session_id="test")

    assert resolved["ok"] is True
    assert resolved["repo"] == "pilotmain/killit"
    assert resolved["source"] == "registry_alias"
    assert resolved["vercel_project"] == "killit"


def test_resolve_explicit_repo_without_registry(isolated_deployment_registry, monkeypatch) -> None:
    from aethos_core.deployment_targets.resolver import resolve_deployment_target

    monkeypatch.setattr(
        "aethos_core.local_workspace.portfolio.extract_filesystem_paths",
        lambda text: [],
    )
    resolved = resolve_deployment_target("deploy acme/widget to vercel from acme/widget")
    assert resolved["ok"] is True
    assert resolved["repo"] == "acme/widget"
    assert resolved["source"] == "chat_repo"


def test_binding_resolution(isolated_deployment_registry) -> None:
    from aethos_core.deployment_targets.bindings import register_binding
    from aethos_core.deployment_targets.registry import register_target
    from aethos_core.deployment_targets.resolver import resolve_deployment_target

    target = register_target(alias="myapp", repo="org/myapp")
    register_binding(target_id=target["target_id"], session_id="solo-user", channel="web", priority=200)

    resolved = resolve_deployment_target("deploy to vercel", session_id="solo-user", channel="web")
    assert resolved["ok"] is True
    assert resolved["source"] == "binding"
    assert resolved["repo"] == "org/myapp"


def test_remote_repo_uses_registry_not_hardcoded_killit(isolated_deployment_registry) -> None:
    from aethos_core.deployment_targets.registry import register_target
    from aethos_core.providers.vercel.greenfield_deployment.remote_repo_source import (
        resolve_remote_github_repo_from_text,
    )

    register_target(alias="killit", repo="pilotmain/killit", vercel_project="killit")

    with patch(
        "aethos_core.providers.vercel.greenfield_deployment.remote_repo_source._lookup_github_repo",
        return_value={
            "ok": True,
            "repo_id": 1,
            "default_branch": "main",
            "html_url": "https://github.com/pilotmain/killit",
            "private": True,
        },
    ):
        remote = resolve_remote_github_repo_from_text("deploy killit to vercel fresh")

    assert remote["ok"] is True
    assert remote["repository"] == "pilotmain/killit"
    assert remote["resolution_source"] == "registry_alias"


def test_killit_without_registry_fails_cleanly(isolated_deployment_registry) -> None:
    from aethos_core.deployment_targets.resolver import clear_session_deploy_targets_for_tests, resolve_deployment_target

    clear_session_deploy_targets_for_tests()
    resolved = resolve_deployment_target("deploy killit to vercel fresh")
    assert resolved["ok"] is False
    assert resolved["blocker_code"] in {
        "DEPLOYMENT_TARGET_UNRESOLVED",
        "DEPLOYMENT_TARGET_NOT_IN_INVENTORY",
        "GITHUB_CREDENTIAL_MISSING",
        "GITHUB_INVENTORY_FAILED",
    }


def test_deploy_resolves_bare_repo_name(isolated_deployment_registry, monkeypatch) -> None:
    from aethos_core.deployment_targets.resolver import (
        clear_session_deploy_targets_for_tests,
        get_session_deploy_target,
        is_railway_greenfield_deploy_continuation,
        merge_greenfield_deploy_continuation_text,
        resolve_deployment_target,
    )

    clear_session_deploy_targets_for_tests()
    monkeypatch.setattr(
        "aethos_core.providers.github.api_client.list_repositories",
        lambda token: {
            "ok": True,
            "repositories": [
                {"full_name": "pilotmain/killit", "name": "killit"},
                {"full_name": "pilotmain/aethos", "name": "aethos"},
            ],
        },
    )
    monkeypatch.setattr(
        "aethos_core.credentials.get_provider_api_token",
        lambda provider, require_validated=True: "gh-test-token" if provider == "github" else None,
    )

    resolved = resolve_deployment_target(
        "deploy killit to railway and set env vars",
        session_id="deploy-bare-name",
    )
    assert resolved["ok"] is True
    assert resolved["repo"] == "pilotmain/killit"
    assert resolved["source"] == "github_inventory"

    pending = get_session_deploy_target("deploy-bare-name")
    assert pending is not None
    assert pending["repo_hint"] == "killit"
    assert pending["repo"] == "pilotmain/killit"

    unknown = resolve_deployment_target("deploy unknown-repo to railway", session_id="deploy-unknown")
    assert unknown["ok"] is False
    assert unknown["blocker_code"] == "DEPLOYMENT_TARGET_NOT_IN_INVENTORY"
    assert "DEPLOYMENT_TARGET_UNRESOLVED" != unknown["blocker_code"]
    assert "connected repos" in str(unknown.get("detail") or "").lower()

    assert is_railway_greenfield_deploy_continuation(
        "github repo is connected already",
        session_id="deploy-bare-name",
    )
    merged = merge_greenfield_deploy_continuation_text(
        "github repo is connected already",
        session_id="deploy-bare-name",
    )
    assert "killit" in merged.lower()
    assert "railway" in merged.lower()


def test_deploy_bare_repo_creates_greenfield_preflight(isolated_deployment_registry, monkeypatch) -> None:
    from aethos_core.deployment_targets.resolver import clear_session_deploy_targets_for_tests
    from aethos_core.providers.railway.greenfield_deployment.greenfield_flow import run_railway_greenfield_deployment_flow

    clear_session_deploy_targets_for_tests()
    checks = {"railway_credential_ok": True, "railway_api_connection_ok": True}
    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        lambda **kwargs: checks,
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.api_client.list_repositories",
        lambda token: {
            "ok": True,
            "repositories": [{"full_name": "pilotmain/killit", "name": "killit"}],
        },
    )
    monkeypatch.setattr(
        "aethos_core.credentials.get_provider_api_token",
        lambda provider, require_validated=True: "gh-test-token" if provider == "github" else None,
    )
    monkeypatch.setattr(
        "aethos_core.production.deployment_mode.is_hosted_deployment",
        lambda: True,
    )
    monkeypatch.setattr(
        "aethos_core.providers.vercel.greenfield_deployment.remote_repo_source._lookup_github_repo",
        lambda repo: {
            "ok": True,
            "default_branch": "main",
            "html_url": "https://github.com/pilotmain/killit",
        },
    )
    monkeypatch.setattr(
        "aethos_core.providers.vercel.greenfield_deployment.remote_repo_inspection.inspect_remote_github_repo_for_deployment",
        lambda **kwargs: {"runtime": "node", "required_env_var_names": ["API_KEY"]},
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.greenfield_flow.create_railway_greenfield_preflight_job",
        lambda **kwargs: {
            "ok": True,
            "preflight_id": "rgf-killit",
            "job_id": "job-killit",
            "job_type": "railway_greenfield_deployment_preflight",
            "steps": [],
            "plan": {"repo": "pilotmain/killit", "service_name": "killit"},
        },
    )
    monkeypatch.setattr(
        "aethos_core.solo_execution.solo_greenfield_executor.maybe_run_solo_greenfield_execution",
        lambda *args, **kwargs: None,
    )

    result = run_railway_greenfield_deployment_flow(
        "deploy killit to railway and set env vars",
        session_id="deploy-preflight-bare",
    )
    assert result.blocked is False
    assert result.preflight_job_id in {"rgf-killit", "job-killit"}
    assert result.artifacts.get("deployment_target", {}).get("repo") == "pilotmain/killit"


def test_cwd_prefix_workspace_resolution(isolated_deployment_registry, tmp_path: Path, monkeypatch) -> None:
    from aethos_core.deployment_targets.registry import register_target
    from aethos_core.local_workspace.registry import register_workspace
    from aethos_core.local_workspace.session_context import resolve_workspace_by_cwd_prefix

    repo = tmp_path / "myrepo"
    repo.mkdir()
    (repo / "package.json").write_text("{}", encoding="utf-8")

    ws = register_workspace(path=str(repo), name="myrepo")
    register_target(alias="myrepo", repo="org/myrepo", workspace_id=ws["workspace_id"], local_path=str(repo))

    nested = repo / "web"
    nested.mkdir()
    match = resolve_workspace_by_cwd_prefix(str(nested))
    assert match is not None
    assert match.get("workspace_id") == ws["workspace_id"]
