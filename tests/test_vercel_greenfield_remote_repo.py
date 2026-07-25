# SPDX-License-Identifier: Apache-2.0
"""Tests for Vercel greenfield remote repo + auth resolution."""

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

    get_settings.cache_clear()
    yield registry_dir
    get_settings.cache_clear()


def test_resolve_vercel_auth_for_chat_includes_token(monkeypatch) -> None:
    from aethos_core.runtime import vercel_readonly_jobs

    class FakeAdapter:
        def resolve_best_auth_method(self, *, operation: str = "read_projects"):
            return {"method": "api_token", "credential_id": "cred-test"}

        def get_api_token(self, credential_id: str) -> str:
            assert credential_id == "cred-test"
            return "vercel-token-abc"

    with patch("aethos_core.providers.vercel.auth.VercelAuthAdapter", FakeAdapter):
        auth = vercel_readonly_jobs.resolve_vercel_auth_for_chat()
    assert auth.get("token") == "vercel-token-abc"
    assert auth.get("auth_method") == "api_token"


def test_remote_repo_resolves_registered_killit(isolated_deployment_registry) -> None:
    from aethos_core.deployment_targets.registry import register_target
    from aethos_core.providers.vercel.greenfield_deployment.remote_repo_source import (
        infer_project_name_from_text,
        resolve_remote_github_repo_from_text,
    )

    register_target(alias="killit", repo="pilotmain/killit", vercel_project="killit")
    assert infer_project_name_from_text("deploy killit to vercel fresh", repo="pilotmain/killit") == "killit"

    with patch(
        "aethos_core.providers.vercel.greenfield_deployment.remote_repo_source._lookup_github_repo",
        return_value={
            "ok": True,
            "repo_id": 1255441182,
            "default_branch": "main",
            "html_url": "https://github.com/pilotmain/killit",
            "private": True,
        },
    ):
        remote = resolve_remote_github_repo_from_text("deploy killit to vercel fresh")
    assert remote["ok"] is True
    assert remote["repository"] == "pilotmain/killit"
    assert remote["project_name"] == "killit"
    assert remote["resolution_source"] == "registry_alias"
