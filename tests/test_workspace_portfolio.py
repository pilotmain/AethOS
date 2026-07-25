# SPDX-License-Identifier: Apache-2.0
"""Tests for workspace portfolio discovery and human-style path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def portfolio_env(tmp_path: Path, monkeypatch):
    portfolio_dir = tmp_path / "portfolio_store"
    portfolio_dir.mkdir()
    monkeypatch.setenv("LOCAL_WORKSPACE_REGISTRY_DIR", str(portfolio_dir))
    monkeypatch.setenv("DEPLOYMENT_TARGETS_REGISTRY_DIR", str(tmp_path / "deployment_targets"))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / ".git").mkdir()
    (path / "package.json").write_text("{}", encoding="utf-8")


def test_discover_projects_under_portfolio_root(portfolio_env, tmp_path: Path) -> None:
    from aethos_core.local_workspace.portfolio import discover_projects, set_portfolio_root

    home = tmp_path / "home"
    _init_git_repo(home / "killit")
    _init_git_repo(home / "nested" / "aethos")

    set_portfolio_root(str(home))
    result = discover_projects(rescan=True, auto_register=False)

    assert result["ok"] is True
    assert result["project_count"] == 2
    names = {row["name"] for row in result["projects"]}
    assert names == {"killit", "aethos"}


def test_find_project_by_name_and_path(portfolio_env, tmp_path: Path) -> None:
    from aethos_core.local_workspace.portfolio import discover_projects, find_project_in_portfolio, set_portfolio_root

    home = tmp_path / "home"
    killit = home / "killit"
    _init_git_repo(killit)
    set_portfolio_root(str(home))
    discover_projects(rescan=True, auto_register=False)

    by_name = find_project_in_portfolio("killit")
    assert by_name is not None
    assert by_name["path"] == str(killit.resolve())

    by_path = find_project_in_portfolio("", text=f"look in {killit}/src")
    assert by_path is not None
    assert by_path["path"] == str(killit.resolve())


def test_resolve_repo_reference_prefers_portfolio_name(portfolio_env, tmp_path: Path) -> None:
    from aethos_core.local_workspace.portfolio import discover_projects, resolve_repo_reference, set_portfolio_root

    home = tmp_path / "home"
    repo = home / "widget"
    _init_git_repo(repo)
    set_portfolio_root(str(home))
    discover_projects(rescan=True, auto_register=False)

    resolved = resolve_repo_reference("show git status for widget")
    assert resolved.get("path") == str(repo.resolve())
    assert resolved.get("source") in {"portfolio_name", "portfolio_name_partial", "registered"}


def test_resolve_git_repo_root_walks_up_from_subdir(portfolio_env, tmp_path: Path) -> None:
    from aethos_core.local_workspace.portfolio import resolve_git_repo_root

    repo = tmp_path / "repo"
    _init_git_repo(repo)
    sub = repo / "web" / "src"
    sub.mkdir(parents=True)

    root = resolve_git_repo_root(sub)
    assert root == repo.resolve()
