# SPDX-License-Identifier: Apache-2.0
"""Regression corpus: help questions never mutate; real commands still preflight."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from aethos_core.chat.explicit_mutation_intent import (
    compose_explicit_mutation_preflight_reply,
    detect_explicit_mutation_intent,
)
from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply
from aethos_core.config import get_settings
from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.runtime.authority import authority
from aethos_core.continuity_intelligence.operational_focus_model import clear_focus_for_tests
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.runtime.jobs import job_store


# §B1 — questions that must NEVER create mutation preflights
INFORMATIONAL_NO_MUTATION = [
    "do you know where to add IMAP or configure it from Mission Control? tell me the exact steps",
    "how do I set environment variables?",
    "where do I add my Railway token?",
    "what can you do?",
    "how does the arbiter work?",
    "explain governed mutations",
    "can you configure email for me?",
    "is it safe to restart my api?",
]


# §B2 — operational commands that MUST still route to preflight
OPERATIONAL_COMMANDS = [
    ("set NODE_ENV=production on killit vercel", "set_env_var", "vercel"),
    ("restart aethos-api on railway", "restart", "railway"),
    ("redeploy killit on vercel", "redeploy", "vercel"),
    ("stop pilot-command-center", "stop", ""),
    ("deploy killit to vercel fresh", "deploy", "vercel"),
]


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_focus_for_tests()
    clear_threads_for_tests()
    job_store.clear_for_tests()
    yield
    clear_focus_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _assert_no_mutation_path(text: str) -> None:
    assert detect_explicit_mutation_intent(text) is None
    assert infer_operation_preflight_intent(text) is None
    assert compose_explicit_mutation_preflight_reply(text) is None
    assert create_mutation_preflight_job_reply(text) is None


@contextmanager
def _resolved_railway_gate(*, service: str = "aethos-api", project: str = "pilotos"):
    def _gate(text, params, operation_type):
        enriched = {
            **params,
            "target_name": service,
            "target_resolved": True,
            "target": {
                "project_name": project,
                "environment": "production",
                "service_name": service,
                "resolved": True,
            },
        }
        return enriched, None

    binding = type("Binding", (), {"ok": True, "stored_github_repo": "", "referenced_github_repo": ""})()

    def _apply_resolution(params, user_text=""):
        return params, type("Resolution", (), {"resolved": True, "detail": None})()

    with patch(
        "aethos_core.chat.mutation_preflight_prompts.gate_railway_mutation_preflight",
        side_effect=_gate,
    ), patch(
        "aethos_core.chat.mutation_target_chat.gate_railway_mutation_preflight",
        side_effect=_gate,
    ), patch(
        "aethos_core.deployment_targets.mutation_resolver.apply_target_resolution_to_params",
        side_effect=_apply_resolution,
    ), patch(
        "aethos_core.provider_topology.binding_verifier.verify_source_binding",
        return_value=binding,
    ):
        yield


@pytest.mark.parametrize("question", INFORMATIONAL_NO_MUTATION)
def test_informational_questions_never_mutate(question: str):
    _assert_no_mutation_path(question)


def test_imap_question_returns_setup_guidance_not_preflight():
    from aethos_core.chat.email_imap_setup_guidance import compose_email_imap_setup_reply_if_applicable

    reply = compose_email_imap_setup_reply_if_applicable(
        "do you know where to add IMAP or configure it from Mission Control? tell me the exact steps",
    )
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "email_imap_setup_guidance"
    assert "IMAP" in body
    assert "Providers" in body
    assert "Email (IMAP/SMTP)" in body
    assert "preflight" not in body.lower()


def test_add_imap_no_longer_matches_vercel_env_intent():
    inferred = infer_operation_preflight_intent(
        "do you know where to add IMAP or configure it from Mission Control?",
    )
    assert inferred is None


@pytest.mark.parametrize("command,operation,provider", OPERATIONAL_COMMANDS)
def test_operational_commands_still_detect_mutation(command: str, operation: str, provider: str):
    intent = detect_explicit_mutation_intent(command)
    assert intent is not None, command
    if operation == "set_env_var":
        assert intent.operation in {"env_update", "set_env_var"}
    else:
        assert intent.operation == operation
    if provider:
        assert intent.provider == provider


def test_restart_railway_service_creates_preflight():
    with _resolved_railway_gate(service="aethos-api"):
        reply = compose_explicit_mutation_preflight_reply("restart aethos-api on railway")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "mutation_preflight_job_created"
    assert "aethos-api" in body
    assert meta.get("proposed_job_id")


def test_set_env_on_vercel_still_infers_preflight():
    inferred = infer_operation_preflight_intent("set NODE_ENV=production on killit vercel")
    assert inferred is not None
    _title, _job_type, params = inferred
    assert params.get("operation_type") == "set_env_var"
    assert params.get("provider") == "vercel"


def test_bare_restart_without_provider_asks_not_defaults_vercel():
    intent = detect_explicit_mutation_intent("restart")
    assert intent is None or intent.provider != "vercel"
    reply = compose_explicit_mutation_preflight_reply("restart")
    if reply is not None:
        _body, reply_intent, _meta = reply
        assert reply_intent in {"mutation_target_clarification", "mutation_provider_clarification"}
