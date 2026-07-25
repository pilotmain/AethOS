# SPDX-License-Identifier: Apache-2.0
"""PROVIDER_DEPLOY_CHAT_TRUTH_ALIGNMENT_FIX regression tests."""

from __future__ import annotations

import pytest

from aethos_core.chat.handlers import deploy_railway_reply, deploy_vercel_reply, resolve_handler
from aethos_core.chat.provider_deploy_capability_intent import (
    detect_provider_deploy_env_capability,
    is_railway_deploy_env_capability_intent,
    is_vercel_deploy_env_capability_intent,
    route_provider_deploy_capability_reply,
)
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.identity.trust_language import LIGHT_TRUST_REMINDER
from aethos_core.runtime.jobs import job_store

RAILWAY_PROMPT = (
    "Can you deploy AethOS to Railway and configure end-to-end environment variables and report back?"
)
VERCEL_PROMPT = (
    "Can you deploy AethOS to Vercel and configure end-to-end environment variables and report back?"
)


@pytest.fixture(autouse=True)
def _clear_jobs():
    job_store.clear_for_tests()
    yield
    job_store.clear_for_tests()


@pytest.fixture(autouse=True)
def _disable_e2e_orchestration(monkeypatch):
    """Truth-alignment tests target capability replies when E2E orchestration is off."""
    monkeypatch.setenv("PROVIDER_E2E_ORCHESTRATION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.parametrize(
    ("prompt", "provider"),
    [
        (RAILWAY_PROMPT, "railway"),
        (VERCEL_PROMPT, "vercel"),
        ("Please deploy my app to Railway with env configuration and verify the result", "railway"),
        ("Could you deploy to Vercel and configure environment variables end-to-end?", "vercel"),
    ],
)
def test_deploy_env_natural_language_matcher(prompt: str, provider: str):
    assert detect_provider_deploy_env_capability(prompt) == provider


def test_deploy_env_matcher_rejects_unrelated_prompt():
    assert detect_provider_deploy_env_capability("explain quantum physics") is None
    assert not is_railway_deploy_env_capability_intent(VERCEL_PROMPT)
    assert not is_vercel_deploy_env_capability_intent(RAILWAY_PROMPT)


def test_route_provider_deploy_capability_reply_meta():
    _reply, intent, meta = route_provider_deploy_capability_reply(RAILWAY_PROMPT)  # type: ignore[misc]
    assert intent == "railway_deploy_capability_truth"
    assert meta.get("suppress_governance_footer") == "true"
    assert meta.get("mutation_performed") == "false"


@pytest.mark.parametrize("prompt", [RAILWAY_PROMPT, VERCEL_PROMPT])
def test_resolve_chat_turn_does_not_use_llm(prompt: str):
    result = resolve_chat_turn(prompt, session_id="provider-deploy-truth", apply_relational_layer=True)
    assert result.used_llm is False
    assert result.intent.endswith("_deploy_capability_truth")
    assert "help plan" not in result.reply.lower()
    assert LIGHT_TRUST_REMINDER not in result.reply


def test_railway_full_chat_truth_content():
    result = resolve_chat_turn(RAILWAY_PROMPT, session_id="railway-full-truth")
    reply = result.reply.lower()
    assert result.intent == "railway_deploy_capability_truth"
    assert "honest answer" in reply
    assert "generic env var" in reply or "set_env_var" in reply
    assert "redeploy" in reply
    assert "restart" in reply
    assert "one-shot" in reply or "one unstructured" in reply
    assert "deployment readiness" in reply


def test_vercel_full_chat_truth_content():
    result = resolve_chat_turn(VERCEL_PROMPT, session_id="vercel-full-truth")
    reply = result.reply.lower()
    assert result.intent == "vercel_deploy_capability_truth"
    assert "honest answer" in reply
    assert "environment variable" in reply or "env var" in reply
    assert "redeploy" in reply
    assert "existing" in reply
    assert "full e2e" in reply
    assert "valid next steps" in reply


def test_resolve_handler_devops_path_matches_railway():
    handled = resolve_handler(RAILWAY_PROMPT, session_id="handler-railway")
    assert handled is not None
    reply, intent, meta = handled
    assert intent == "railway_deploy_capability_truth"
    assert meta.get("suppress_governance_footer") == "true"


def test_no_job_or_mutation_created_for_capability_questions():
    before = len(job_store.list_all())
    resolve_chat_turn(RAILWAY_PROMPT, session_id="no-mutation-railway")
    resolve_chat_turn(VERCEL_PROMPT, session_id="no-mutation-vercel")
    assert len(job_store.list_all()) == before


def test_deploy_vercel_reply_level_2_contract():
    reply = deploy_vercel_reply()
    assert "Vercel capability — honest answer" in reply
    assert "environment variable" in reply.lower()
    assert "redeploy" in reply.lower()
    assert "help plan and inspect" not in reply.lower()


def test_deploy_railway_reply_contract():
    reply = deploy_railway_reply()
    assert "Railway capability — honest answer" in reply
    assert "generic env var" in reply.lower() or "set_env_var" in reply.lower()
    assert "redeploy" in reply.lower()
    assert "fix 112" in reply.lower()
