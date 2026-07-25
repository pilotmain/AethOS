# SPDX-License-Identifier: Apache-2.0
"""AethOS soul and memory contract tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.aethos_identity.continuity_decision import compose_continuity_operational_reply
from aethos_core.aethos_identity.context_reconstructor import (
    ProviderTargetMatch,
    TopologySearchResult,
    search_provider_targets,
)
from aethos_core.aethos_identity.memory_contract import load_memory_markdown, memory_layers
from aethos_core.aethos_identity.self_consistency_guard import should_block_generic_fallback
from aethos_core.aethos_identity.soul_contract import load_soul_markdown, soul_doctrines
from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_threads_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def test_soul_md_exists_and_contains_operational_doctrine():
    text = load_soul_markdown()
    assert text
    assert "governed operational intelligence partner" in text.lower()
    doctrines = soul_doctrines()
    assert any("reconstruct before asking" in d.lower() for d in doctrines)


def test_memory_md_exists_and_contains_memory_hierarchy():
    text = load_memory_markdown()
    assert text
    layers = memory_layers()
    assert "Active operational thread" in layers
    assert "Job truth ledger" in layers
    assert "Provider topology memory" in text


def test_generic_fallback_blocked_for_known_service():
    assert should_block_generic_fallback(
        text="can you check top 5 logs and its timestamp for pilotos-api?",
        session_id="block-generic",
    )


@patch("aethos_core.aethos_identity.continuity_decision._fetch_readonly_logs")
def test_context_reconstructed_from_service_name(mock_logs):
    mock_logs.return_value = [
        {"timestamp": "2026-05-20T12:00:00+00:00", "level": "INFO", "message": "Application startup complete."},
        {"timestamp": "2026-05-20T11:59:00+00:00", "level": "INFO", "message": "Boot line"},
    ]
    reply = compose_continuity_operational_reply(
        "can you check top 5 logs and its timestamp for pilotos-api?",
        session_id="reconstruct-service",
    )
    assert reply is not None
    body, intent, meta = reply
    assert "pilotos-api" in body
    assert "don't have an active operational mutation thread" not in body.lower()
    assert intent in {"continuity_readonly_logs", "actionable_check_logs", "provider_followup_fetch_top_n_logs"}
    assert meta.get("service") == "pilotos-api"


@patch("aethos_core.aethos_identity.continuity_decision._fetch_readonly_logs")
def test_readonly_log_check_works_without_active_thread(mock_logs):
    mock_logs.return_value = [
        {"timestamp": "2026-05-20T12:01:00+00:00", "level": "INFO", "message": "ready"},
    ]
    reply = compose_continuity_operational_reply(
        "show recent logs for speakglobal-ai",
        session_id="readonly-no-thread",
    )
    assert reply is not None
    body, intent, _meta = reply
    assert "speakglobal-ai" in body
    assert "Latest" in body or "logs" in body.lower()
    assert "don't have an active operational mutation thread" not in body.lower()


def test_expired_thread_reconstructs_from_provider_topology():
    topology = search_provider_targets("pilotos-api")
    assert topology.resolved is not None
    assert topology.resolved.provider == "railway"
    assert topology.resolved.project_name == "pilotos"


def test_ambiguous_provider_asks_targeted_clarification():
    ambiguous = TopologySearchResult(
        phrase="demo-api",
        ambiguous=True,
        matches=[
            ProviderTargetMatch(provider="railway", service_name="demo-api", project_name="pilotos", path="pilotos / production / demo-api"),
            ProviderTargetMatch(provider="vercel", service_name="demo-api", path="demo-api"),
        ],
    )
    with patch(
        "aethos_core.aethos_identity.context_reconstructor.search_provider_targets",
        return_value=ambiguous,
    ):
        reply = compose_continuity_operational_reply(
            "check logs for demo-api",
            session_id="ambiguous-provider",
        )
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "continuity_provider_clarification"
    assert "Which provider should I check" in body


@patch("aethos_core.aethos_identity.continuity_decision._fetch_readonly_logs")
def test_api_route_avoids_stale_thread_reply(mock_logs,):
    mock_logs.return_value = [
        {"timestamp": "2026-05-20T12:00:00+00:00", "level": "INFO", "message": "Application startup complete."},
    ]
    from aethos_core.api.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "can you check top 5 logs and its timestamp for pilotos-api?",
            "session_id": "api-no-thread",
        },
    )
    body = response.json()
    assert "don't have an active operational mutation thread" not in body["reply"].lower()
    assert "pilotos-api" in body["reply"]
