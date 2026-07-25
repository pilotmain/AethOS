# SPDX-License-Identifier: Apache-2.0
"""Source binding store consistency tests."""

from __future__ import annotations

from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.source_binding_resolver import (
    check_stale_binding_regression,
    compose_stale_binding_regression_reply,
    refresh_params_source_binding,
    resolve_source_binding_for_service,
)
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, save_binding
from aethos_core.task_frame.pending_action import clear_pending_actions_for_tests, offer_retry_preflight_action


def setup_function():
    clear_topology_for_tests()
    clear_pending_actions_for_tests()


def test_binding_update_persists_to_canonical_resolver():
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
    resolution = resolve_source_binding_for_service(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service="speakglobal-ai",
    )
    assert resolution.github_repo == "pilotmain/speakglobal-ai"
    assert resolution.verified is True
    assert resolution.resolution_source == "confirmed_binding"


def test_canonical_binding_overrides_stale_inventory():
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
    resolution = resolve_source_binding_for_service(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service="speakglobal-ai",
        job_params={"source_binding": "rayameresa/speakglobal-ai"},
    )
    assert resolution.github_repo == "pilotmain/speakglobal-ai"
    assert resolution.resolution_source == "confirmed_binding"


def test_canonical_binding_overrides_old_job_params():
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
    params = {
        "provider": "railway",
        "operation_type": "restart",
        "target_name": "speakglobal-ai",
        "target": {"project_name": "adequate-luck", "environment": "production", "service_name": "speakglobal-ai"},
        "source_binding": "rayameresa/speakglobal-ai",
    }
    refreshed, resolution, regression = refresh_params_source_binding(params, block_stale_regression=True)
    assert resolution.github_repo == "pilotmain/speakglobal-ai"
    assert refreshed["source_binding"] == "pilotmain/speakglobal-ai"
    assert regression is not None
    assert regression.attempted_repo == "rayameresa/speakglobal-ai"


def test_execution_never_uses_stale_repo_after_update():
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
    offer_retry_preflight_action(
        session_id="consistency",
        provider="railway",
        project="adequate-luck",
        environment="production",
        service="speakglobal-ai",
        operation="restart",
        source_binding="pilotmain/speakglobal-ai",
    )
    resolution = resolve_source_binding_for_service(
        provider="railway",
        project="adequate-luck",
        environment="production",
        service="speakglobal-ai",
        session_id="consistency",
    )
    assert resolution.github_repo == "pilotmain/speakglobal-ai"
    assert "rayameresa" not in (resolution.github_repo or "")


def test_stale_binding_regression_guard_blocks_execution():
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
    regression = check_stale_binding_regression(
        resolve_source_binding_for_service(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service="speakglobal-ai",
        ),
        "rayameresa/speakglobal-ai",
    )
    assert regression is not None
    reply = compose_stale_binding_regression_reply(regression)
    assert "Blocked stale source binding regression" in reply
    assert "pilotmain/speakglobal-ai" in reply
    assert "rayameresa/speakglobal-ai" in reply
