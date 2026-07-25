# SPDX-License-Identifier: Apache-2.0
"""PROVIDER_E2E_READINESS_RESPONSE_HARDENING regression tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.identity.trust_language import LIGHT_TRUST_REMINDER
from aethos_core.provider_e2e_readiness.blocker_mapping import (
    ReadinessBlocker,
    map_plain_text_blocker,
    map_railway_blockers,
)
from aethos_core.provider_e2e_readiness.readiness_intent import (
    detect_provider_e2e_readiness_kind,
    is_provider_e2e_readiness_intent,
    is_railway_provider_e2e_readiness_intent,
    is_vercel_provider_e2e_readiness_intent,
)
from aethos_core.provider_e2e_readiness.readiness_router import route_provider_e2e_readiness
from aethos_core.runtime.jobs import job_store

RAILWAY_READINESS_PROMPT = "Check if AethOS is ready to deploy to Railway."
RAILWAY_E2E_PROMPT = (
    "Can you deploy AethOS to Railway and configure end-to-end environment variables and report back?"
)
VERCEL_READINESS_PROMPT = "Check if AethOS is ready to deploy to Vercel."
VERCEL_BLOCKING_PROMPT = "What is blocking Vercel deployment?"


@pytest.fixture(autouse=True)
def _clear_jobs():
    job_store.clear_for_tests()
    yield
    job_store.clear_for_tests()


@pytest.mark.parametrize(
    "prompt",
    [
        RAILWAY_READINESS_PROMPT,
        "Is AethOS ready for Railway deployment?",
        "Check Railway deployment readiness.",
        "Can Railway deploy AethOS right now?",
        "What is blocking Railway deployment?",
        "Is the Railway service configured?",
    ],
)
def test_railway_readiness_intent_matcher(prompt: str):
    assert is_railway_provider_e2e_readiness_intent(prompt)
    assert is_provider_e2e_readiness_intent(prompt)
    assert detect_provider_e2e_readiness_kind(prompt) == "railway"


@pytest.mark.parametrize(
    "prompt",
    [
        VERCEL_READINESS_PROMPT,
        "Is AethOS ready for Vercel deployment?",
        "Check Vercel deployment readiness.",
        VERCEL_BLOCKING_PROMPT,
    ],
)
def test_vercel_readiness_intent_matcher(prompt: str):
    assert is_vercel_provider_e2e_readiness_intent(prompt)
    assert is_provider_e2e_readiness_intent(prompt)
    assert detect_provider_e2e_readiness_kind(prompt) == "vercel"


def test_e2e_execution_prompt_is_not_readiness_only():
    assert not is_provider_e2e_readiness_intent(RAILWAY_E2E_PROMPT)


@patch(
    "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks"
)
def test_railway_readiness_structured_report(mock_checks):
    mock_checks.return_value = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "railway_credential_source": "canonical resolver",
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": True, "project_count": 1, "service_count": 1, "projects": []},
        "service_creation": {"env_var_writes_enabled": True},
    }
    with patch("aethos_core.config.get_settings") as mock_settings:
        settings = mock_settings.return_value
        settings.mutation_execution_enabled = False
        settings.provider_env_var_mutations_enabled = True
        result = route_provider_e2e_readiness(RAILWAY_READINESS_PROMPT, session_id="hardening-railway")
    assert result is not None
    body, intent, meta = result
    assert intent == "provider_e2e_readiness_report"
    assert "Railway Deployment Readiness" in body
    assert "### 1. Overall readiness" in body
    assert "### 7. Blockers" in body
    assert "### 8. Safe next steps" in body
    assert meta.get("preflight_created") == "false"
    assert meta.get("mutation_performed") == "false"


def test_railway_readiness_chat_route_no_llm():
    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks._resolve_railway_token_canonical",
        return_value=(None, "test", "missing token"),
    ):
        result = resolve_chat_turn(RAILWAY_READINESS_PROMPT, session_id="hardening-readiness-chat")
    assert result.used_llm is False
    assert result.intent == "provider_e2e_readiness_report"
    assert "Railway Deployment Readiness" in result.reply
    assert "missing context" not in result.reply.lower()
    assert "help plan" not in result.reply.lower()
    assert LIGHT_TRUST_REMINDER not in result.reply


def test_railway_e2e_not_authorized_maps_to_actionable_blocker():
    checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": False,
        "railway_api_connection_detail": "Not Authorized",
    }
    blockers = map_railway_blockers(checks, settings=object(), include_mutation_gates=False)
    assert blockers[0].code == "RAILWAY_TOKEN_INVALID"
    assert blockers[0].required_action
    assert blockers[0].safe_next_command

    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks._resolve_railway_token_canonical",
        return_value=("bad-token", "test", "ok"),
    ), patch(
        "aethos_core.providers.railway.api_client.test_connection",
        return_value={"ok": False, "detail": "Not Authorized"},
    ):
        result = resolve_chat_turn(RAILWAY_E2E_PROMPT, session_id="hardening-not-authorized")

    assert result.used_llm is False
    assert result.intent in {"railway_e2e_missing_config", "execution_brain_recovery"}
    assert "Not Authorized" not in result.reply
    assert "validate Railway connection" in result.reply
    assert "Mutation performed" not in result.reply
    if result.intent == "railway_e2e_missing_config":
        assert "RAILWAY_TOKEN_INVALID" in result.reply
        assert "Required action:" in result.reply
    else:
        assert "token validation failed" in result.reply.lower()
        assert "After that succeeds I can" in result.reply
    assert LIGHT_TRUST_REMINDER not in result.reply


def test_vercel_readiness_chat_route_no_llm():
    with patch(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.resolve_best_auth_method",
        return_value={"method": "none", "detail": "no token"},
    ):
        result = resolve_chat_turn(VERCEL_READINESS_PROMPT, session_id="hardening-vercel-readiness")
    assert result.used_llm is False
    assert result.intent == "provider_e2e_readiness_report"
    assert "Vercel Deployment Readiness" in result.reply
    assert "### 2. Provider connection" in result.reply


def test_readiness_does_not_create_preflight_job():
    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks._resolve_railway_token_canonical",
        return_value=(None, "test", "missing"),
    ):
        resolve_chat_turn(RAILWAY_READINESS_PROMPT, session_id="hardening-no-preflight")
    assert job_store.list_all() == []


def test_no_secrets_in_readiness_or_missing_config_replies():
    secret = "rw_live_super_secret_token_value"
    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks._resolve_railway_token_canonical",
        return_value=(secret, "test", "ok"),
    ), patch(
        "aethos_core.providers.railway.api_client.test_connection",
        return_value={"ok": False, "detail": "Not Authorized"},
    ):
        readiness = resolve_chat_turn(RAILWAY_READINESS_PROMPT, session_id="hardening-secrets-readiness")
        missing = resolve_chat_turn(RAILWAY_E2E_PROMPT, session_id="hardening-secrets-e2e")
    for reply in (readiness.reply, missing.reply):
        assert secret not in reply
        assert "rw_live" not in reply


def test_map_plain_text_not_authorized():
    blocker = map_plain_text_blocker("Not Authorized", provider="railway")
    assert blocker.code == "RAILWAY_TOKEN_INVALID"
    assert isinstance(blocker, ReadinessBlocker)
