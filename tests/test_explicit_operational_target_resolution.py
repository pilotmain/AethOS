# SPDX-License-Identifier: Apache-2.0
"""Generic explicit operational target resolution tests."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from aethos_core.conversation.provider_memory.conversational_memory_router import compose_provider_followup_reply
from aethos_core.operational_target_resolution.explicit_target_resolver import (
    explicit_target_overrides_session_context,
    resolve_explicit_operational_target,
    should_route_explicit_provider_diagnostics,
)
from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, save_thread_state
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.post_mutation_verification.global_verification_preemption import (
    route_global_verification_query,
    should_preempt_to_post_mutation_verification,
)
from aethos_core.runtime.jobs import job_store
from tests.test_global_verification_preemption import _seed_execution_job


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    job_store.clear_for_tests()


def _seed_railway_greenfield_thread(session_id: str) -> None:
    save_thread_state(
        OperationalThreadState(
            session_id=session_id,
            active_thread="railway_greenfield_deployment",
            provider="railway",
            project="pilotos",
            environment="staging",
            service="aethos-ui",
            operation="greenfield_deploy",
            status="deploy_live",
            updated_at=datetime.now(tz=UTC).isoformat(),
        )
    )


def test_resolve_registry_alias_without_hardcoded_project_list() -> None:
    row = {
        "target_id": "dt-test",
        "alias": "my-saas",
        "repo": "acme/my-saas",
        "vercel_project": "my-saas-prod",
        "default_provider": "vercel",
    }
    with patch(
        "aethos_core.deployment_targets.registry.match_aliases_in_text",
        return_value=row,
    ):
        target = resolve_explicit_operational_target("check the error for my-saas and report back")
    assert target is not None
    assert target.provider == "vercel"
    assert target.vercel_project == "my-saas-prod"
    assert target.has_diagnostic_intent is True


def test_vercel_killit_overrides_railway_thread_and_verification() -> None:
    session_id = "explicit-target-killit"
    _seed_railway_greenfield_thread(session_id)
    _seed_execution_job(session_id=session_id, service="influencer-crm")

    prompt = "can you check if there is any error logs for killit in vercel and report back the health?"
    assert explicit_target_overrides_session_context(prompt, session_id=session_id) is True
    assert should_preempt_to_post_mutation_verification(prompt, session_id=session_id) is False
    assert compose_provider_followup_reply(prompt, session_id=session_id) is None

    verification = route_global_verification_query(prompt, session_id=session_id)
    assert verification is None


def test_early_provider_diagnostics_route_returns_killit_project() -> None:
    session_id = "explicit-target-route"
    _seed_railway_greenfield_thread(session_id)
    prompt = "check health for killit on vercel"
    killit_row = {
        "target_id": "dt-killit",
        "alias": "killit",
        "vercel_project": "killit",
        "default_provider": "vercel",
    }
    with patch(
        "aethos_core.deployment_targets.registry.match_aliases_in_text",
        return_value=killit_row,
    ), patch(
        "aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat",
        return_value={"auth_method": "api_token", "credential_id": "vercel-cred"},
    ), patch(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token",
        return_value="test-token",
    ), patch(
        "aethos_core.providers.vercel.operations.deployments_api.fetch_deployments",
        return_value={
            "ok": True,
            "deployments": [{"created_at": "t", "state": "READY", "branch": "main", "url": "https://killit.vercel.app"}],
        },
    ):
        result = route_operational_conversation_kernel_turn(prompt, session_id=session_id)

    assert result is not None
    assert result.meta.get("readonly_provider") == "vercel"
    assert "killit" in result.reply
    assert "Railway" not in result.reply
    assert "influencer-crm" not in result.reply


def test_top_logs_for_killit_routes_to_vercel_before_railway_health_context() -> None:
    session_id = "explicit-target-killit-logs"
    _seed_railway_greenfield_thread(session_id)
    killit_row = {
        "target_id": "dt-killit",
        "alias": "killit",
        "repo": "pilotmain/killit",
        "vercel_project": "killit",
        "default_provider": "vercel",
    }
    prompt = "give me top 5 logs for killit?"
    evidence = {
        "ok": True,
        "operation": "logs",
        "project_name": "killit",
        "project": {"ok": True, "details": {"framework": "nextjs", "repo_link": "pilotmain/killit"}},
        "latest_deployment": {"state": "ready", "branch": "main", "commit": "abc", "url": "https://killit.vercel.app"},
        "build_analysis": {"summary": "Build ok.", "error_lines": []},
        "runtime_analysis": {"summary": "Runtime ok.", "runtime_lines": ["GET / 200"]},
        "domain_health": {"ok": True, "summary": "1/1 reachable.", "checks": []},
        "env_metadata": {"skipped": True},
        "github_correlation": {"lines": []},
    }
    with patch(
        "aethos_core.deployment_targets.registry.match_aliases_in_text",
        return_value=killit_row,
    ), patch(
        "aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat",
        return_value={
            "auth_method": "api_token",
            "credential_id": "vercel-cred",
            "profile_id": None,
            "block_reason": None,
        },
    ), patch(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token",
        return_value="test-token",
    ), patch(
        "aethos_core.providers.vercel.operations.logs_api.fetch_deployment_logs",
        return_value={
            "ok": True,
            "project_name": "killit",
            "events": [{"created": "2026-06-01T10:00:00Z", "type": "stdout", "text": "GET / 200"}],
            "log_lines": [],
        },
    ):
        result = route_operational_conversation_kernel_turn(prompt, session_id=session_id)

    assert result is not None
    assert result.meta.get("readonly_provider") == "vercel"
    assert "killit" in result.reply
    assert "aethos-api" not in result.reply
    assert "aethos-ui" not in result.reply


def test_railway_redeploy_request_does_not_route_to_vercel_diagnostics() -> None:
    session_id = "railway-redeploy-block"
    _seed_railway_greenfield_thread(session_id)
    prompt = (
        "can you check AethOS changes in git hub and redeploy latest commits to "
        "railway stage for both UI and API changes?"
    )
    assert should_route_explicit_provider_diagnostics(prompt, session_id=session_id) is False
    assert should_preempt_to_post_mutation_verification(prompt, session_id=session_id) is False


def test_for_both_is_not_a_vercel_project_hint() -> None:
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import (
        extract_vercel_project_hint,
        mentions_explicit_readonly_provider,
    )

    prompt = "redeploy latest commits to railway stage for both UI and API changes"
    assert extract_vercel_project_hint(prompt) == ""
    assert mentions_explicit_readonly_provider(prompt) is None


def test_primary_provider_prefers_railway_on_redeploy() -> None:
    from aethos_core.operational_target_resolution.provider_intent_guard import primary_explicit_provider

    prompt = "check github and redeploy to railway staging"
    assert primary_explicit_provider(prompt) == "railway"


def test_should_route_explicit_provider_diagnostics_for_named_project() -> None:
    assert should_route_explicit_provider_diagnostics(
        "inspect deployment health for invoicepilot on vercel",
        session_id="default",
    )
