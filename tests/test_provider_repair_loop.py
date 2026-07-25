# SPDX-License-Identifier: Apache-2.0
"""Provider repair loop tests."""

from __future__ import annotations

import pytest

from aethos_core.provider_topology.repair_loop import compose_repair_proposal, execute_topology_repair
from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, get_binding, save_binding


@pytest.fixture(autouse=True)
def _clean():
    clear_topology_for_tests()
    yield
    clear_topology_for_tests()


def test_missing_installation_repair_proposal():
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            github_repo="rayameresa/speakglobal-ai",
        )
    )
    repair = compose_repair_proposal(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
        user_text="fix the repo binding and retry",
        failure_reason="No GitHub installation found for repo: rayameresa/speakglobal-ai",
        accessible_repos=["pilotmain/speakglobal-ai"],
    )
    assert "stale repository mapping" in repair["reply"].lower() or "installation" in repair["reply"].lower()
    assert "refresh provider topology" in repair["reply"].lower()
    assert repair["meta"]["provider"] == "railway"


def test_stale_repo_binding_proposes_update():
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            github_repo="rayameresa/speakglobal-ai",
        )
    )
    repair = compose_repair_proposal(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
        user_text="use pilotmain/speakglobal-ai and retry",
        failure_reason="No GitHub installation found for repo: rayameresa/speakglobal-ai",
        accessible_repos=["pilotmain/speakglobal-ai"],
    )
    assert "pilotmain/speakglobal-ai" in repair["reply"]
    assert "Approval is required" in repair["reply"]


def test_refresh_and_retry_updates_binding():
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            github_repo="rayameresa/speakglobal-ai",
        )
    )
    outcome = execute_topology_repair(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
        github_repo="pilotmain/speakglobal-ai",
    )
    assert outcome["ok"] is True
    binding = get_binding(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
    )
    assert binding is not None
    assert binding.github_repo == "pilotmain/speakglobal-ai"


def test_governed_repair_requires_approval_language():
    repair = compose_repair_proposal(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
        failure_reason="installation missing",
    )
    assert "Approval is required" in repair["reply"]
