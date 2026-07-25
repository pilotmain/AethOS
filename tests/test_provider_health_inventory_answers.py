# SPDX-License-Identifier: Apache-2.0
"""Acceptance tests for provider health inventory + follow-up routing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.informational_help_router import (
    is_canned_general_help_blurb,
    route_informational_help_turn,
)
from aethos_core.chat.provider_read_intent import (
    compose_provider_health_followup_reply,
    compose_provider_read_inventory_reply,
    try_compose_inventory_rerender_reply,
)
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.response_composition.operational_result_store import clear_operational_results_for_tests


@pytest.fixture(autouse=True)
def _clean_results():
    clear_operational_results_for_tests()
    yield
    clear_operational_results_for_tests()


VERCEL_PROJECTS = [
    {
        "name": "lifeos",
        "id": "prj_1",
        "framework": "nextjs",
        "latest_production_state": "ready",
        "production_url": "lifeos.vercel.app",
        "health": "healthy",
    },
    {
        "name": "killit",
        "id": "prj_2",
        "framework": "nextjs",
        "latest_production_state": "error",
        "production_url": "killit.vercel.app",
        "health": "failed",
    },
]

RAILWAY_INVENTORY = {
    "provider": "railway",
    "projects": [
        {
            "name": "pilotos",
            "id": "proj-1",
            "environments": [
                {
                    "name": "staging",
                    "id": "env-1",
                    "services": [
                        {
                            "name": "aethos-api",
                            "id": "svc-1",
                            "type": "web",
                            "status": "running",
                            "latest_deployment": {"id": "dep-1", "status": "SUCCESS", "url": "api.up.railway.app"},
                        },
                        {
                            "name": "aethos-ui",
                            "id": "svc-2",
                            "type": "web",
                            "status": "failed",
                            "latest_deployment": {"id": "dep-2", "status": "FAILED", "url": ""},
                        },
                    ],
                }
            ],
        }
    ],
}


def _mock_vercel_inventory():
    return patch(
        "aethos_core.execution_brain.provider_agent_ops.provider_inventory",
        return_value={
            "ok": True,
            "provider": "vercel",
            "inventory": {
                "provider": "vercel",
                "project_count": 2,
                "projects": VERCEL_PROJECTS,
            },
        },
    )


def _mock_railway_inventory():
    return patch(
        "aethos_core.execution_brain.provider_agent_ops.provider_inventory",
        return_value={
            "ok": True,
            "provider": "railway",
            "inventory": RAILWAY_INVENTORY,
        },
    )


def test_vercel_list_with_health_returns_table_not_unknown_wall():
    with _mock_vercel_inventory():
        body, intent, meta = compose_provider_read_inventory_reply(
            "list all Vercel projects with health as a table",
            session_id="health-vercel-list",
        )
    assert intent == "provider_read_inventory"
    assert meta.get("provider") == "vercel"
    assert "| Project | Service | Type | Health | Domain |" in body
    assert "| lifeos |" in body
    assert "| healthy |" in body
    assert "| failed |" in body
    assert "unknown" not in body.lower().split("| health |")[1].split("\n")[0]


def test_railway_list_with_health_returns_table_not_json():
    with _mock_railway_inventory():
        body, intent, _meta = compose_provider_read_inventory_reply(
            "list all Railway projects with health as a table",
            session_id="health-railway-list",
        )
    assert intent == "provider_read_inventory"
    assert "| Project | Service | Type | Health | Domain |" in body
    assert "| aethos-api |" in body
    assert "| healthy |" in body
    assert "| failed |" in body
    assert "```json" not in body


def test_why_is_health_unknown_not_informational_blurb():
    session_id = "health-why-unknown"
    with _mock_vercel_inventory():
        compose_provider_read_inventory_reply(
            "list all Vercel projects with health",
            session_id=session_id,
        )
        reply = compose_provider_health_followup_reply("why is health unknown?", session_id=session_id)
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "provider_health_unknown_explain"
    assert is_canned_general_help_blurb(body) is False
    assert "DEPLOYMENT_MODE" not in body
    routed = route_informational_help_turn("why is health unknown?", session_id=session_id)
    assert routed is None


def test_check_health_runs_and_reports_per_service():
    session_id = "health-check-vercel"
    health_payload = {
        "ok": True,
        "projects": [
            {
                "project_name": "lifeos",
                "latest_production_state": "ready",
                "latest_deployment_state": "ready",
                "latest_url": "lifeos.vercel.app",
            },
            {
                "project_name": "killit",
                "latest_production_state": "error",
                "latest_deployment_state": "error",
                "latest_url": "killit.vercel.app",
            },
        ],
    }
    with _mock_vercel_inventory(), patch(
        "aethos_core.execution_brain.provider_agent_ops.provider_health",
        return_value={"ok": True, "provider": "vercel", "health": health_payload},
    ):
        reply = compose_provider_health_followup_reply(
            "actually check the health, healthy or failed?",
            session_id=session_id,
        )
    assert reply is not None
    body, intent, meta = reply
    assert intent == "provider_health_check"
    assert meta.get("provider") == "vercel"
    assert "healthy" in body.lower()
    assert "failed" in body.lower()
    assert is_canned_general_help_blurb(body) is False


def test_make_it_a_table_reformats_prior_inventory():
    session_id = "health-table-followup"
    with _mock_railway_inventory():
        compose_provider_read_inventory_reply(
            "list all Railway projects with health",
            session_id=session_id,
        )
        reply = try_compose_inventory_rerender_reply("make it a table instead", session_id=session_id)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "provider_inventory_rerender"
    assert meta.get("from_cache") == "true"
    assert "| aethos-api |" in body
    assert "| healthy |" in body
    assert "```json" not in body


def test_resolve_chat_turn_vercel_health_question_not_blurb():
    session_id = "health-chat-turn"
    with _mock_vercel_inventory():
        result = resolve_chat_turn("why is health unknown?", session_id=session_id, apply_relational_layer=False)
    assert result is not None
    assert is_canned_general_help_blurb(result.reply) is False
    assert "railway" not in result.reply.lower() or "vercel" in result.reply.lower()
