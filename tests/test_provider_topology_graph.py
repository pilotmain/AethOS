# SPDX-License-Identifier: Apache-2.0
"""Provider topology graph tests."""

from __future__ import annotations

import pytest

from aethos_core.provider_topology.ambiguity_detection import detect_binding_ambiguity
from aethos_core.provider_topology.binding_verifier import verify_source_binding
from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, save_binding
from aethos_core.provider_topology.topology_refresh import refresh_service_topology


@pytest.fixture(autouse=True)
def _clean():
    clear_topology_for_tests()
    yield
    clear_topology_for_tests()


def _seed_speakglobal_binding() -> SourceBinding:
    binding = SourceBinding(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
        service_id="svc-speakglobal",
        github_repo="rayameresa/speakglobal-ai",
        domains=["speakglobal.ai"],
    )
    save_binding(binding)
    return binding


def test_railway_github_binding_graph():
    binding = _seed_speakglobal_binding()
    graph = refresh_service_topology(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
    )
    assert graph is not None
    assert graph.service.service_name == "speakglobal-ai"
    assert graph.source is not None
    assert graph.source.repo == binding.github_repo


def test_stale_repo_mapping_detected():
    _seed_speakglobal_binding()
    result = verify_source_binding(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
        user_text="please use pilotmain/speakglobal-ai",
        accessible_repos=["pilotmain/speakglobal-ai"],
    )
    assert result.ok is False
    assert result.stored_github_repo == "rayameresa/speakglobal-ai"
    assert result.referenced_github_repo == "pilotmain/speakglobal-ai"
    assert result.failure_stage == "source_binding"


def test_installation_mismatch_detected():
    _seed_speakglobal_binding()
    ambiguity = detect_binding_ambiguity(
        stored_repo="rayameresa/speakglobal-ai",
        user_text="restart speakglobal-ai",
        accessible_repos=["pilotmain/speakglobal-ai"],
    )
    assert ambiguity is not None
    assert ambiguity.kind == "installation_mismatch"
    assert ambiguity.referenced_repo == "pilotmain/speakglobal-ai"


def test_topology_refresh_updates_binding():
    _seed_speakglobal_binding()
    graph = refresh_service_topology(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
        github_repo="pilotmain/speakglobal-ai",
        force=True,
    )
    assert graph is not None
    assert graph.source is not None
    assert graph.source.repo == "pilotmain/speakglobal-ai"


def test_ambiguity_detection_repo_mismatch():
    ambiguity = detect_binding_ambiguity(
        stored_repo="rayameresa/speakglobal-ai",
        user_text="check https://github.com/pilotmain/speakglobal-ai",
        accessible_repos=["pilotmain/speakglobal-ai", "rayameresa/speakglobal-ai"],
    )
    assert ambiguity is not None
    assert ambiguity.kind == "repo_mismatch"
    assert ambiguity.referenced_repo == "pilotmain/speakglobal-ai"
