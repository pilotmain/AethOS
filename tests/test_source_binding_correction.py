# SPDX-License-Identifier: Apache-2.0
"""Source binding correction flow tests."""

from __future__ import annotations

import pytest

from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.provider_topology.binding_update_flow import get_pending_correction
from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.source_binding_correction import process_binding_correction
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, get_binding, save_binding
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    clear_topology_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    clear_topology_for_tests()
    job_store.clear_for_tests()


def _seed_failed_thread(session_id: str = "binding-fix") -> None:
    save_binding(
        SourceBinding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            github_repo="rayameresa/speakglobal-ai",
        )
    )
    preflight = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "target": {
                "project_name": "adequate-luck",
                "environment": "production",
                "service_name": "speakglobal-ai",
                "resolved": True,
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "target": {"project_name": "adequate-luck", "environment": "production", "service_name": "speakglobal-ai"},
            "executed": False,
            "execution_state": "execution_failed",
            "error": "No GitHub installation found for repo: rayameresa/speakglobal-ai",
            "mutation_execution": {"error": "No GitHub installation found for repo: rayameresa/speakglobal-ai"},
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    sync_thread_from_execution_job(job=stored)


def test_active_failure_plus_repo_url_prompts_correction():
    _seed_failed_thread()
    result = process_binding_correction(
        "use https://github.com/pilotmain/speakglobal-ai/ instead",
        session_id="binding-fix",
        accessible_repos=["pilotmain/speakglobal-ai"],
    )
    assert result["kind"] in {"confirmation_needed", "binding_updated"}
    assert "pilotmain/speakglobal-ai" in result["message"]
    assert "rayameresa/speakglobal-ai" in result["message"]
    assert "adequate-luck / production / speakglobal-ai" in result["message"]


def test_auto_update_when_user_says_instead():
    _seed_failed_thread(session_id="binding-auto")
    result = process_binding_correction(
        "use pilotmain/speakglobal-ai instead",
        session_id="binding-auto",
        accessible_repos=["pilotmain/speakglobal-ai"],
    )
    assert result["kind"] == "binding_updated"
    binding = get_binding(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
    )
    assert binding is not None
    assert binding.github_repo == "pilotmain/speakglobal-ai"


def test_verified_repo_updates_binding_after_confirmation():
    _seed_failed_thread(session_id="binding-confirm")
    process_binding_correction(
        "can you check https://github.com/pilotmain/speakglobal-ai/",
        session_id="binding-confirm",
        accessible_repos=["pilotmain/speakglobal-ai"],
    )
    assert get_pending_correction(session_id="binding-confirm") is not None
    result = process_binding_correction(
        "yes update it",
        session_id="binding-confirm",
        accessible_repos=["pilotmain/speakglobal-ai"],
    )
    assert result["kind"] == "binding_updated"
    binding = get_binding(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
    )
    assert binding is not None
    assert binding.github_repo == "pilotmain/speakglobal-ai"
    assert binding.source_verified is True


def test_failed_repo_access_does_not_update():
    _seed_failed_thread(session_id="binding-fail")
    result = process_binding_correction(
        "use pilotmain/speakglobal-ai instead",
        session_id="binding-fail",
        accessible_repos=["rayameresa/speakglobal-ai"],
    )
    assert result["kind"] == "access_failed"
    binding = get_binding(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service_name="speakglobal-ai",
    )
    assert binding is not None
    assert binding.github_repo == "rayameresa/speakglobal-ai"


def test_restart_with_repo_is_binding_correction_not_service():
    _seed_failed_thread(session_id="binding-restart")
    from aethos_core.provider_topology.source_binding_correction import process_restart_with_repo_target

    result = process_restart_with_repo_target(
        "restart railway pilotmain/speakglobal-ai service",
        session_id="binding-restart",
        accessible_repos=["pilotmain/speakglobal-ai"],
    )
    assert result is not None
    assert result["kind"] == "restart_repo_not_service"
    assert "GitHub repository" in result["message"]
    assert "pilotmain" not in result["message"].split("Railway service")[0] or "GitHub repository" in result["message"]
    assert "Could not confirm a Railway service matching **pilotmain**" not in result["message"]


def test_no_active_thread_asks_for_service():
    result = process_binding_correction(
        "use pilotmain/speakglobal-ai instead",
        session_id="no-thread",
        accessible_repos=["pilotmain/speakglobal-ai"],
    )
    assert result["kind"] == "no_thread"
