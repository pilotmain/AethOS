# SPDX-License-Identifier: Apache-2.0
"""LOCAL_WORKSPACE_CANONICAL_PATH_FIX tests."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.local_workspace.canonical_path import (
    evaluate_workspace_path,
    infer_canonical_repo_root,
    is_mutation_artifact_path,
    is_recursive_mutation_artifact_path,
    iter_repo_files_limited,
    path_should_be_skipped_for_scan,
)
from aethos_core.local_workspace.registry import register_workspace, resolve_workspace_path
from aethos_core.local_workspace.scanner import scan_workspace_stack
from aethos_core.providers.railway.greenfield_deployment.greenfield_flow import run_railway_greenfield_deployment_flow
from aethos_core.providers.railway.greenfield_deployment.local_workspace_source import (
    discover_local_workspace_deployment_source,
)
from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import resolve_git_remote_from_workspace

GREENFIELD_PROMPT = (
    "AethOS is a new project. Check local workspace, get its remote git, "
    "create a new Railway project, deploy, set required env vars, and report back."
)
_LIST_SERVICES_PATCH = "aethos_core.providers.railway.credential_truth.list_services_with_status"


def _init_repo(root, *, remote: str | None = "git@github.com:pilotmain/AethOS.git") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "aethos_core").mkdir(exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='aethos'\n", encoding="utf-8")
    (root / "tests").mkdir(exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "ops@example.com"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "AethOS Test"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)
    if remote:
        subprocess.run(["git", "remote", "add", "origin", remote], cwd=root, check=True, capture_output=True)


def _inventory_ok(token, *args, **kwargs):
    _ = (token, args, kwargs)
    return {"ok": True, "services": [], "error": None}


def test_recursive_mutation_workspace_path_is_rejected(tmp_path):
    canonical = tmp_path / "AethOS"
    _init_repo(canonical)
    nested = (
        canonical
        / "data/agent_artifacts/mutation_workspaces/mws-deadbeef/repo/data/agent_artifacts/mutation_workspaces/mws-cafe/repo"
    )
    nested.mkdir(parents=True)

    assert is_recursive_mutation_artifact_path(nested)
    evaluation = evaluate_workspace_path(nested)
    assert evaluation.ok is False
    assert evaluation.blocker_code == "LOCAL_WORKSPACE_RECURSIVE_ARTIFACT_PATH"


def test_canonical_repo_root_is_discovered_from_single_mutation_sandbox(tmp_path):
    canonical = tmp_path / "AethOS"
    _init_repo(canonical)
    sandbox = canonical / "data/agent_artifacts/mutation_workspaces/mws-deadbeef/repo"
    sandbox.mkdir(parents=True)

    assert is_mutation_artifact_path(sandbox)
    assert not is_recursive_mutation_artifact_path(sandbox)
    inferred = infer_canonical_repo_root(sandbox)
    assert inferred == canonical.resolve()


def test_artifact_folders_are_excluded_from_scan(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    artifacts = repo / "data/agent_artifacts/mutation_workspaces/mws-123/repo/deep/nested/file.py"
    artifacts.parent.mkdir(parents=True, exist_ok=True)
    artifacts.write_text("print('artifact')\n", encoding="utf-8")
    (repo / "aethos_core" / "real.py").write_text("print('real')\n", encoding="utf-8")

    assert path_should_be_skipped_for_scan(artifacts)
    scanned = list(iter_repo_files_limited(repo, max_depth=8))
    scanned_paths = {str(path.relative_to(repo)) for path in scanned}
    assert "aethos_core/real.py" in scanned_paths
    assert not any("mutation_workspaces" in path for path in scanned_paths)
    stack = scan_workspace_stack(repo)
    assert "python" in stack.get("languages", [])


def test_register_workspace_rejects_mutation_artifact_path(tmp_path):
    repo = tmp_path / "AethOS"
    _init_repo(repo)
    sandbox = repo / "data/agent_artifacts/mutation_workspaces/mws-deadbeef/repo"
    sandbox.mkdir(parents=True)

    with pytest.raises(ValueError, match="generated mutation workspace"):
        register_workspace(path=str(sandbox))


@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch):
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_greenfield_deploy_returns_recursive_artifact_blocker(tmp_path, monkeypatch):
    repo = tmp_path / "AethOS"
    _init_repo(repo)
    recursive = (
        repo
        / "data/agent_artifacts/mutation_workspaces/mws-a/repo/data/agent_artifacts/mutation_workspaces/mws-b/repo"
    )
    recursive.mkdir(parents=True)
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(recursive))

    source = discover_local_workspace_deployment_source(hint="aethos")
    assert source["ok"] is False
    assert source["blocker_code"] == "LOCAL_WORKSPACE_RECURSIVE_ARTIFACT_PATH"
    assert "Errno 63" not in str(source.get("detail") or "")


def test_greenfield_deploy_canonicalizes_single_mutation_sandbox(tmp_path, monkeypatch):
    repo = tmp_path / "AethOS"
    _init_repo(repo)
    sandbox = repo / "data/agent_artifacts/mutation_workspaces/mws-deadbeef/repo"
    sandbox.mkdir(parents=True)
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(sandbox))

    source = discover_local_workspace_deployment_source(hint="aethos")
    assert source["ok"] is True
    assert source["canonicalized"] is True
    assert source["workspace_root"] == str(repo.resolve())

    remote = resolve_git_remote_from_workspace(source["workspace_root"])
    assert remote["ok"] is True
    assert "AethOS" in str(remote.get("repository") or "")
    assert remote["remote_url"]


def test_greenfield_flow_does_not_bubble_errno_63(tmp_path, monkeypatch):
    repo = tmp_path / "AethOS"
    _init_repo(repo)
    recursive = (
        repo
        / "data/agent_artifacts/mutation_workspaces/mws-a/repo/data/agent_artifacts/mutation_workspaces/mws-b/repo"
    )
    recursive.mkdir(parents=True)
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(recursive))

    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        result = run_railway_greenfield_deployment_flow(GREENFIELD_PROMPT, session_id="canonical-path")

    assert result.blocker_code == "LOCAL_WORKSPACE_RECURSIVE_ARTIFACT_PATH"
    assert "File name too long" not in result.reply
    assert "Errno 63" not in result.reply


def test_resolve_chat_turn_reports_recursive_blocker_not_cogerr(tmp_path, monkeypatch):
    repo = tmp_path / "AethOS"
    _init_repo(repo)
    recursive = (
        repo
        / "data/agent_artifacts/mutation_workspaces/mws-a/repo/data/agent_artifacts/mutation_workspaces/mws-b/repo"
    )
    recursive.mkdir(parents=True)
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(recursive))

    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        chat = resolve_chat_turn(GREENFIELD_PROMPT, session_id="canonical-chat", apply_relational_layer=False)

    assert chat.meta.get("blocker_code") == "LOCAL_WORKSPACE_RECURSIVE_ARTIFACT_PATH"
    assert "recalling the" not in chat.reply.lower()
    assert "Errno 63" not in chat.reply


def test_resolve_workspace_path_prefers_canonical_root(tmp_path, monkeypatch):
    repo = tmp_path / "AethOS"
    _init_repo(repo)
    sandbox = repo / "data/agent_artifacts/mutation_workspaces/mws-deadbeef/repo"
    sandbox.mkdir(parents=True)
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(sandbox))

    resolved = resolve_workspace_path("aethos")
    assert resolved == repo.resolve()
