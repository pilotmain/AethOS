# SPDX-License-Identifier: Apache-2.0
"""OPERATIONAL_CONVERSATION_KERNEL_001 — multi-turn certification scripts."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.operational_session import clear_operational_sessions_for_tests
from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn
from aethos_core.operational_session.operational_session import load_operational_session


@pytest.fixture(autouse=True)
def _clean_sessions():
    clear_operational_sessions_for_tests()
    yield
    clear_operational_sessions_for_tests()


@pytest.fixture(autouse=True)
def _disable_llm_refinement():
    with patch(
        "aethos_core.execution_brain.goal_llm_refiner.maybe_refine_operational_goal",
        side_effect=lambda plan, **_: plan,
    ), patch(
        "aethos_core.execution_brain.goal_llm_refiner.maybe_refine_operational_reply",
        side_effect=lambda reply, **_: (reply, False),
    ):
        yield


@pytest.fixture
def enable_kernel(monkeypatch):
    from aethos_core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "operational_conversation_kernel_enabled", True)
    monkeypatch.setattr(settings, "execution_brain_use_llm", False)
    monkeypatch.setattr(settings, "use_real_llm", False)


def _health_rows():
    return [
        {
            "service": "aethos-api",
            "project": "pilotos",
            "environment": "staging",
            "status": "running",
            "health": "healthy",
            "deployment_state": "success",
            "service_id": "svc-api",
        },
        {
            "service": "aethos-ui",
            "project": "pilotos",
            "environment": "staging",
            "status": "running",
            "health": "healthy",
            "deployment_state": "success",
            "service_id": "svc-ui",
        },
    ]


def test_railway_inventory_then_logs_follow_up(enable_kernel):
    inventory = {
        "ok": True,
        "project_count": 1,
        "service_count": 2,
        "environment_count": 1,
        "projects": [{"name": "pilotos", "services": ["aethos-api", "aethos-ui"]}],
    }
    checks = {"railway_credential_ok": True, "railway_api_connection_ok": True, "inventory": inventory}

    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        return_value=checks,
    ):
        turn1 = route_operational_conversation_kernel_turn("show Railway projects", session_id="kernel-railway")
    assert turn1 is not None
    assert turn1.meta.get("route_id") == "operational_conversation_kernel"
    assert "pilotos" in turn1.reply.lower() or "projects" in turn1.reply.lower()

    session = load_operational_session(session_id="kernel-railway")
    assert session.subject.provider == "railway"

    def _fake_fetch(*, service_name: str, limit: int = 5, **kwargs):
        return {
            "ok": True,
            "logs": [
                {
                    "timestamp": "2026-06-01T12:00:00Z",
                    "level": "INFO",
                    "message": f"{service_name} line",
                    "source": "deployment_logs",
                }
            ],
            "sources_checked": ["deployment_logs"],
        }

    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
        return_value=(_health_rows(), None),
    ), patch(
        "aethos_core.providers.railway.operations.logs_multisource.fetch_railway_service_logs_fast",
        side_effect=_fake_fetch,
    ):
        turn2 = route_operational_conversation_kernel_turn("show logs", session_id="kernel-railway")
        turn3 = route_operational_conversation_kernel_turn("top 5 only", session_id="kernel-railway")
        turn4 = route_operational_conversation_kernel_turn("what about api?", session_id="kernel-railway")

    assert turn2 is not None
    assert "aethos-api line" in turn2.reply or "aethos-ui line" in turn2.reply
    assert turn3 is not None
    assert "line" in turn3.reply
    assert turn4 is not None
    assert "aethos-api line" in turn4.reply
    assert "aethos-ui" not in turn4.reply


def test_killit_vercel_logs_and_follow_up(enable_kernel):
    killit_row = {
        "target_id": "dt-killit",
        "alias": "killit",
        "repo": "pilotmain/killit",
        "vercel_project": "killit",
        "default_provider": "vercel",
    }
    log_payload = {
        "ok": True,
        "project_name": "killit",
        "deployment_id": "dpl_123",
        "deployment": {"state": "ready"},
        "events": [
            {"created": "2026-06-01T10:00:00Z", "type": "stdout", "text": "GET / 200"},
            {"created": "2026-06-01T10:00:01Z", "type": "stdout", "text": "ready"},
        ],
        "log_lines": [],
        "api_limited": False,
    }

    with patch(
        "aethos_core.deployment_targets.registry.match_aliases_in_text",
        return_value=killit_row,
    ), patch(
        "aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat",
        return_value={"auth_method": "api_token", "credential_id": "cred-1"},
    ), patch(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token",
        return_value="token",
    ), patch(
        "aethos_core.providers.vercel.operations.logs_api.fetch_deployment_logs",
        return_value=log_payload,
    ):
        turn1 = route_operational_conversation_kernel_turn(
            "give me top 5 logs for killit?",
            session_id="kernel-killit",
        )
        turn2 = route_operational_conversation_kernel_turn(
            "but i asked for top 5 logs right, can you give me that?",
            session_id="kernel-killit",
        )

    assert turn1 is not None
    assert turn1.meta.get("readonly_provider") == "vercel"
    assert "killit" in turn1.reply
    assert "GET / 200" in turn1.reply
    assert "aethos-api" not in turn1.reply

    assert turn2 is not None
    assert turn2.meta.get("readonly_provider") == "vercel"
    assert "killit" in turn2.reply.lower() or "GET / 200" in turn2.reply
    assert "aethos-api" not in turn2.reply


def test_kernel_blocks_mutation_intent(enable_kernel):
    result = route_operational_conversation_kernel_turn(
        "redeploy aethos-api on railway",
        session_id="kernel-mutation",
    )
    assert result is None
