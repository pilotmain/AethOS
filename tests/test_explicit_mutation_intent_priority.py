# SPDX-License-Identifier: Apache-2.0
"""Explicit mutation intent routing priority tests."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from aethos_core.chat.explicit_mutation_intent import (
    compose_explicit_mutation_preflight_reply,
    detect_explicit_mutation_intent,
)
from aethos_core.continuity_intelligence.operational_focus_model import clear_focus_for_tests
from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, save_thread_state
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.operational_thread_memory.thread_persistence import _expires_at
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store
from datetime import UTC, datetime


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


@contextmanager
def _resolved_railway_gate(*, service: str = "pilotos-api", project: str = "pilotos"):
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


def test_restart_railway_pilotos_api_detects_mutation_intent():
    intent = detect_explicit_mutation_intent("restart the railway pilotos-api")
    assert intent is not None
    assert intent.operation == "restart"
    assert intent.provider == "railway"
    assert intent.target_phrase == "pilotos-api"
    assert intent.confidence >= 0.75


def test_restart_railway_pilotos_api_creates_preflight():
    with _resolved_railway_gate():
        reply = compose_explicit_mutation_preflight_reply(
            "restart the railway pilotos-api",
            session_id="explicit-restart",
        )
    assert reply is not None
    body, intent, meta = reply
    assert intent == "mutation_preflight_job_created"
    assert "pilotos-api" in body
    assert "governed restart preflight" in body.lower()
    assert "no restart has been performed yet" in body.lower()
    assert meta.get("proposed_job_id")


def test_restart_with_active_inspect_context_creates_preflight():
    save_thread_state(
        OperationalThreadState(
            session_id="inspect-restart",
            provider="railway",
            project="pilotos",
            environment="production",
            service="pilotos-api",
            operation="inspect",
            status="reconstructed_from_topology",
            last_system_result="Reconstructed provider context for pilotos-api.",
            updated_at=datetime.now(UTC).isoformat(),
            expires_at=_expires_at(),
        )
    )
    with _resolved_railway_gate():
        reply = compose_explicit_mutation_preflight_reply("restart", session_id="inspect-restart")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "mutation_preflight_job_created"
    assert "pilotos-api" in body
    assert "continuing" not in body.lower()
    assert "inspect thread" not in body.lower()


def test_check_logs_remains_readonly_intent():
    assert detect_explicit_mutation_intent("check logs for pilotos-api") is None


def test_did_restart_happen_remains_readonly_intent():
    assert detect_explicit_mutation_intent("did the restart happen?") is None


def test_ambiguous_restart_asks_which_target():
    authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "target": {"project_name": "pilotos", "environment": "production", "service_name": "pilotos-api"},
        },
        source="test",
        session_id="ambiguous-restart",
        auto_run=False,
    )
    authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "target": {"project_name": "adequate-luck", "environment": "production", "service_name": "speakglobal-ai"},
        },
        source="test",
        session_id="ambiguous-restart",
        auto_run=False,
    )
    reply = compose_explicit_mutation_preflight_reply("restart", session_id="ambiguous-restart")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "mutation_target_clarification"
    assert "Which one should I restart?" in body
    assert "No preflight has been created yet" in body
