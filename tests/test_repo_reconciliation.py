# SPDX-License-Identifier: Apache-2.0
"""Repository rename / transfer reconciliation tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.provider_topology.repo_reconciliation import (
    compose_reconciliation_reply,
    detect_repo_redirect,
    read_local_git_remote,
    reconcile_source_binding,
    refresh_binding_from_remote,
)
from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, get_binding, save_binding


def setup_function():
    clear_topology_for_tests()


def test_read_local_git_remote_parses_github_url(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    with patch(
        "aethos_core.provider_topology.repo_reconciliation.subprocess.run",
        return_value=type("Proc", (), {"returncode": 0, "stdout": "https://github.com/pilotmain/speakglobal-ai.git", "stderr": ""})(),
    ):
        info = read_local_git_remote(str(repo))
    assert info.ok is True
    assert info.owner_repo == "pilotmain/speakglobal-ai"


def test_detect_repo_redirect_finds_accessible_owner_change():
    with patch(
        "aethos_core.provider_topology.repo_reconciliation.verify_github_repo_access",
        side_effect=lambda repo, accessible_repos=None: type(
            "Access",
            (),
            {"ok": repo == "pilotmain/speakglobal-ai", "repo": repo, "message": repo},
        )(),
    ):
        with patch(
            "aethos_core.provider_topology.repo_reconciliation._detect_github_api_redirect",
            return_value=None,
        ):
            result = detect_repo_redirect(
                "rayameresa/speakglobal-ai",
                accessible_repos=["pilotmain/speakglobal-ai"],
            )
    assert result.redirected is True
    assert result.current_repo == "pilotmain/speakglobal-ai"
    assert result.current_accessible is True


def test_canonical_binding_overrides_stale_layers():
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            github_repo="pilotmain/speakglobal-ai",
            source_verified=True,
        )
    )
    with patch(
        "aethos_core.provider_topology.repo_reconciliation.verify_github_repo_access",
        side_effect=lambda repo, accessible_repos=None: type("Access", (), {"ok": True, "repo": repo, "message": "ok"})(),
    ):
        with patch(
            "aethos_core.provider_topology.repo_reconciliation.detect_repo_redirect",
            return_value=type(
                "Redirect",
                (),
                {
                    "old_repo": "rayameresa/speakglobal-ai",
                    "redirected": True,
                    "current_repo": "pilotmain/speakglobal-ai",
                    "current_accessible": True,
                    "message": "redirect",
                    "to_dict": lambda self: {},
                },
            )(),
        ):
            with patch(
                "aethos_core.provider_topology.repo_reconciliation.read_local_git_remote",
                return_value=type(
                    "Remote",
                    (),
                    {
                        "ok": True,
                        "owner_repo": "pilotmain/speakglobal-ai",
                        "message": "local",
                        "to_dict": lambda self: {},
                    },
                )(),
            ):
                with patch(
                    "aethos_core.provider_topology.repo_reconciliation.read_railway_service_source_metadata",
                    return_value=type(
                        "Railway",
                        (),
                        {
                            "linked_repo": "rayameresa/speakglobal-ai",
                            "stale": True,
                            "message": "stale railway",
                            "to_dict": lambda self: {},
                        },
                    )(),
                ):
                    result = reconcile_source_binding(
                        project="adequate-luck",
                        environment="production",
                        service_name="speakglobal-ai",
                        old_repo="rayameresa/speakglobal-ai",
                        candidate_repo="pilotmain/speakglobal-ai",
                    )
    assert result.confirmed_repo == "pilotmain/speakglobal-ai"
    assert "provider_topology_binding" not in result.stale_locations
    assert "railway_service_metadata" in result.stale_locations
    reply = compose_reconciliation_reply(result)
    assert "pilotmain/speakglobal-ai" in reply
    assert "rayameresa/speakglobal-ai" in reply
    assert "Railway note" in reply


def test_refresh_binding_from_remote_updates_canonical_store(tmp_path):
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            github_repo="rayameresa/speakglobal-ai",
        )
    )
    with patch(
        "aethos_core.provider_topology.repo_reconciliation.read_local_git_remote",
        return_value=type(
            "Remote",
            (),
            {"ok": True, "owner_repo": "pilotmain/speakglobal-ai", "message": "local", "to_dict": lambda self: {}},
        )(),
    ):
        with patch(
            "aethos_core.provider_topology.repo_reconciliation.verify_github_repo_access",
            side_effect=lambda repo, accessible_repos=None: type("Access", (), {"ok": True, "repo": repo, "message": "ok"})(),
        ):
            with patch(
                "aethos_core.provider_topology.repo_reconciliation.detect_repo_redirect",
                return_value=type(
                    "Redirect",
                    (),
                    {
                        "old_repo": "rayameresa/speakglobal-ai",
                        "redirected": True,
                        "current_repo": "pilotmain/speakglobal-ai",
                        "current_accessible": True,
                        "message": "redirect",
                        "to_dict": lambda self: {},
                    },
                )(),
            ):
                with patch(
                    "aethos_core.provider_topology.repo_reconciliation.read_railway_service_source_metadata",
                    return_value=type(
                        "Railway",
                        (),
                        {"linked_repo": None, "stale": False, "message": "none", "to_dict": lambda self: {}},
                    )(),
                ):
                    result = refresh_binding_from_remote(
                        project="adequate-luck",
                        environment="production",
                        service_name="speakglobal-ai",
                        confirm=True,
                    )
    assert result.updated is True
    binding = get_binding(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
    )
    assert binding is not None
    assert binding.github_repo == "pilotmain/speakglobal-ai"
    assert binding.source_verified is True


def test_stale_repo_owner_never_used_after_reconciliation():
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            github_repo="pilotmain/speakglobal-ai",
            source_verified=True,
        )
    )
    from aethos_core.provider_topology.source_binding_resolver import resolve_source_binding_for_service

    resolution = resolve_source_binding_for_service(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service="speakglobal-ai",
        job_params={"source_binding": "rayameresa/speakglobal-ai"},
    )
    assert resolution.github_repo == "pilotmain/speakglobal-ai"
    assert "rayameresa" not in (resolution.github_repo or "")
