# SPDX-License-Identifier: Apache-2.0
"""Vercel list routing — single loop owns provider-read intents."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.provider_read_intent import contains_deflection_runaround
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _single_loop(monkeypatch):
    monkeypatch.setattr(get_settings(), "chat_single_loop_enabled", True)
    get_settings.cache_clear()


def _mock_vercel_inventory(*_args, **_kwargs):
    return {
        "ok": True,
        "provider": "vercel",
        "inventory": {
            "project_count": 2,
            "projects": [
                {"name": "alpha-app", "health": "healthy", "production_url": "https://alpha.example"},
                {"name": "beta-app", "health": "failed", "production_url": "https://beta.example"},
            ],
        },
    }


def test_list_vercel_projects_table_in_chat():
    with patch(
        "aethos_core.execution_brain.provider_agent_ops.provider_inventory",
        side_effect=_mock_vercel_inventory,
    ):
        result = resolve_chat_turn(
            "List all Vercel projects with health status in a table",
            session_id="vercel-route-1",
        )
    assert "alpha-app" in result.reply
    assert "beta-app" in result.reply
    assert "|" in result.reply
    assert not contains_deflection_runaround(result.reply)
    assert result.intent == "provider_read_inventory"


def test_give_list_here_in_chat():
    from aethos_core.chat.job_result_followup_router import compose_job_result_followup_reply
    from aethos_core.runtime.authority import authority
    from aethos_core.runtime.jobs import JobStatus, job_store

    job = authority.create_job(
        title="Vercel inventory",
        job_type="vercel_projects_inventory",
        params={},
        source="chat",
        session_id="vercel-route-2",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.params["vercel_inventory"] = {
        "projects": [
            {"name": "alpha-app", "health": "healthy", "production_url": "https://alpha.example"},
        ],
    }
    stored.status = JobStatus.COMPLETED
    job_store.complete_with_result(
        job.id,
        full_result="inventory complete",
        summary="done",
        preview="done",
        provider="none",
        model="",
        used_llm=False,
        fallback=False,
    )
    handled = compose_job_result_followup_reply(
        "just give me the list here in the chat",
        session_id="vercel-route-2",
    )
    assert handled is not None
    body, intent, _meta = handled
    assert "alpha-app" in body
    assert not contains_deflection_runaround(body)


def test_token_present_inventory_succeeds():
    with patch(
        "aethos_core.execution_brain.provider_agent_ops.provider_inventory",
        side_effect=_mock_vercel_inventory,
    ):
        result = resolve_chat_turn("list my Vercel projects", session_id="vercel-route-3")
    assert result.intent == "provider_read_inventory"
    assert "revoked" not in result.reply.lower()


def test_missing_token_honest_message():
    def _fail_inventory(*_args, **_kwargs):
        return {"ok": False, "error": "vercel_token_not_configured", "provider": "vercel"}

    with patch(
        "aethos_core.execution_brain.provider_agent_ops.provider_inventory",
        side_effect=_fail_inventory,
    ):
        result = resolve_chat_turn("show my Vercel projects", session_id="vercel-route-4")
    assert result.intent == "provider_read_inventory_failed"
    assert "inventory failed" in result.reply.lower()
    assert not contains_deflection_runaround(result.reply)
