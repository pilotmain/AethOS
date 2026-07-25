# SPDX-License-Identifier: Apache-2.0
"""Provider readonly intent routing tests."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.conversation.provider_memory.conversational_memory_router import compose_provider_followup_reply
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, save_thread_state
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.provider_readonly_intent.readonly_provider_router import route_readonly_provider_question
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    job_store.clear_for_tests()


def _seed_active_railway_thread(session_id: str) -> None:
    preflight = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "MongoDB",
            "target": {
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
                "service_name": "MongoDB",
                "resolved": True,
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    save_thread_state(
        OperationalThreadState(
            session_id=session_id,
            provider="railway",
            project="pilotcore-sales-engine",
            environment="production",
            service="MongoDB",
            operation="restart",
            status="stabilizing",
            updated_at=datetime.now(tz=UTC).isoformat(),
        )
    )


@contextmanager
def _github_auth_and_repo(*, repo: str = "pilotmain/aethos"):
    evidence = {
        "ok": True,
        "repository": repo,
        "operation": "repo_status",
        "repo": {
            "ok": True,
            "repository": repo,
            "default_branch": "main",
            "private": False,
            "pushed_at": "2026-05-20T00:00:00Z",
        },
        "branch": {
            "ok": True,
            "repository": repo,
            "branch": "main",
            "sha": "abc123def456",
            "committed_at": "2026-05-20T00:00:00Z",
            "protected": False,
        },
        "divergence": {"ok": True, "base": "main", "head": "main", "ahead_by": 0, "behind_by": 0, "status": "identical"},
        "local_changes_note": "Remote branch compare shows no divergence on the inspected refs.",
        "commits": {"ok": True, "commits": []},
        "checks": {"ok": True, "failed_count": 0, "checks": []},
        "workflow_runs": {"ok": True, "runs": []},
        "workflow_diagnostic": {"ok": True, "latest_failed_run": None},
        "workflow_jobs": {"ok": True, "failed_jobs": []},
        "pull_requests": {"ok": True, "pull_requests": []},
        "releases": {"ok": True, "latest_release": None, "latest_tag": None},
        "deploy_correlation": {"lines": ["No cached Railway/Vercel failure correlated with this repo yet."], "deploy_related_failures": 0},
    }
    with patch(
        "aethos_core.runtime.github_readonly_jobs.resolve_github_auth_for_chat",
        return_value={"auth_method": "api_token", "credential_id": "gh-cred", "block_reason": None},
    ), patch(
        "aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token",
        return_value="test-token",
    ), patch(
        "aethos_core.providers.github.diagnostics.github_live_diagnostics.collect_github_live_evidence",
        return_value=evidence,
    ):
        yield


def test_github_prompt_preempts_railway_thread() -> None:
    session_id = "readonly-gh-thread"
    _seed_active_railway_thread(session_id)

    with _github_auth_and_repo():
        result = route_readonly_provider_question(
            "can you inspect my GitHub repo status for pilotmain/aethos?",
            session_id=session_id,
        )
    assert result is not None
    assert result.meta.get("route_id") == "provider_readonly_intent"
    assert result.meta.get("readonly_provider") == "github"
    assert "Continuing the active Railway" not in result.reply
    assert "Default branch" in result.reply
    assert compose_provider_followup_reply(
        "can you inspect my GitHub repo status for pilotmain/aethos?",
        session_id=session_id,
    ) is None


def test_github_repo_missing_asks_targeted_clarification() -> None:
    result = route_readonly_provider_question("can you inspect my GitHub repo status?", session_id="readonly-gh-missing")
    assert result is not None
    assert "Which GitHub repo should I inspect?" in result.reply
    assert "pilotmain/aethos" in result.reply


def test_vercel_prompt_preempts_railway_thread_and_runs_readonly_job() -> None:
    session_id = "readonly-vercel-thread"
    _seed_active_railway_thread(session_id)

    evidence = {
        "ok": True,
        "operation": "deployments",
        "project_name": "lifeos",
        "project": {"ok": True, "details": {"framework": "nextjs", "repo_link": "pilotmain/lifeos", "production_url": "lifeos.vercel.app"}},
        "latest_deployment": {"state": "ready", "created_at": "2026-05-20", "branch": "main", "commit": "abc123", "url": "https://lifeos.vercel.app"},
        "failed_deployment": None,
        "build_analysis": {"summary": "No build error lines detected."},
        "runtime_analysis": {"summary": "No runtime error lines detected."},
        "domain_health": {"ok": True, "summary": "1/1 checked domain(s) reachable.", "checks": []},
        "env_metadata": {"skipped": True},
        "github_correlation": {"lines": []},
        "deployments": {"ok": True, "deployments": []},
        "logs": {"ok": True, "log_lines": []},
    }
    with patch(
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
        "aethos_core.providers.vercel.diagnostics.vercel_live_diagnostics.collect_vercel_live_evidence",
        return_value=evidence,
    ):
        result = route_readonly_provider_question("can you inspect Vercel deployments for lifeos?", session_id=session_id)
    assert result is not None
    assert result.meta.get("readonly_provider") == "vercel"
    assert result.meta.get("vercel_live_diagnostics") == "true"
    assert "Vercel deployment guidance" not in result.reply
    assert "deployment:" in result.reply.lower()


def test_vercel_killit_error_check_preempts_railway_greenfield_thread() -> None:
    session_id = "readonly-vercel-killit"
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
    from aethos_core.conversation.provider_memory.conversational_memory_router import compose_provider_followup_reply
    from aethos_core.operational_thread_memory.thread_reply_composer import compose_operational_thread_followup
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import (
        classify_vercel_readonly_intent,
        should_yield_active_thread_for_readonly,
    )

    prompt_with_vercel = "can you check the error for killit in vercel and fix anything needed and report back?"
    assert should_yield_active_thread_for_readonly(prompt_with_vercel) is True
    intent = classify_vercel_readonly_intent(prompt_with_vercel)
    assert intent is not None
    assert intent.provider == "vercel"
    assert intent.project == "killit"
    assert compose_operational_thread_followup(prompt_with_vercel, session_id=session_id) is None
    assert compose_provider_followup_reply(prompt_with_vercel, session_id=session_id) is None

    prompt_without_vercel = "can you check the error for killit and fix anything needed and report back?"
    assert should_yield_active_thread_for_readonly(prompt_without_vercel) is True
    assert classify_vercel_readonly_intent(prompt_without_vercel) is not None
    assert compose_provider_followup_reply(prompt_without_vercel, session_id=session_id) is None


def test_vercel_greenfield_intent_matches_deploy_killit_from_remote_repo() -> None:
    from aethos_core.providers.vercel.greenfield_deployment.greenfield_intent import (
        is_vercel_greenfield_deployment_intent,
    )

    prompt = (
        "deploye killit from remot repo to vercel and setup all env var required "
        "and let me know the final report?"
    )
    assert is_vercel_greenfield_deployment_intent(prompt) is True


def test_vercel_blocked_runtime_gives_exact_blocker() -> None:
    with patch(
        "aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat",
        return_value={"auth_method": None, "credential_id": None, "profile_id": None, "block_reason": "missing"},
    ), patch(
        "aethos_core.runtime.browser_capability.get_browser_capability_status",
        return_value={
            "enabled": False,
            "execution_ready": False,
            "execution_label": "Playwright runtime not ready",
        },
    ), patch(
        "aethos_core.runtime.browser_runtime.browser_inventory_refresh_blocked_reason",
        return_value=(True, "Playwright runtime not ready"),
    ), patch(
        "aethos_core.runtime.vercel_readonly_jobs.saved_vercel_profile_auth_for_chat",
        return_value=None,
    ), patch(
        "aethos_core.chat.vercel_readonly_prompts.create_vercel_readonly_job_reply",
        return_value=None,
    ):
        result = route_readonly_provider_question("can you inspect Vercel deployments?", session_id="readonly-vercel-blocked")
    assert result is not None
    assert result.intent == "vercel_readonly_blocked"
    assert "Vercel readonly execution is blocked" in result.reply
    assert "Playwright/browser runtime not ready" in result.reply
    assert "VERCEL_API_TOKEN missing" in result.reply


def test_readonly_prompt_does_not_create_mutation_preflight() -> None:
    session_id = "readonly-no-preflight"
    _seed_active_railway_thread(session_id)
    prompt = "can you inspect my GitHub repo status?"
    assert create_mutation_preflight_job_reply(prompt, session_id=session_id) is None

    before_preflights = {
        job.id
        for job in job_store.list_all()
        if job.session_id == session_id and job.job_type == "mutation_preflight"
    }
    with _github_auth_and_repo():
        resolve_chat_turn(prompt, session_id=session_id, apply_relational_layer=False)
    after_preflights = [
        job
        for job in job_store.list_all()
        if job.session_id == session_id and job.job_type == "mutation_preflight"
    ]
    assert {job.id for job in after_preflights} == before_preflights
