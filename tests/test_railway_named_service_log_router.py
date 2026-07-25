# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.operational_session.railway_service_hints import (
    is_railway_named_service_log_request,
)
from aethos_core.post_mutation_verification.global_verification_preemption import is_global_verification_query
from aethos_core.post_mutation_verification.verification_intent_router import classify_verification_intent
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture
def health_rows():
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


def _seed_health_context(session_id: str, rows: list[dict]):
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": rows},
        summary={"total": len(rows), "healthy": len(rows), "failed": 0, "unknown": 0},
        scope="named_service_health",
        meta={"route_id": "multi_provider_health", "matched_services": "aethos-api,aethos-ui"},
    )


def test_top_five_logs_for_each_is_named_service_log_request(health_rows):
    _seed_health_context("logs-session", health_rows)
    text = "give me top 5 logs for each"
    assert is_railway_named_service_log_request(text, session_id="logs-session")


def test_health_status_log_followup_is_named_service_log_request(health_rows):
    _seed_health_context("logs-session", health_rows)
    text = "give me some logs that shows the health status please"
    assert is_railway_named_service_log_request(text, session_id="logs-session")


def test_named_service_log_request_blocks_verification(health_rows):
    _seed_health_context("logs-session", health_rows)
    text = "give me top 5 logs for each"
    assert classify_verification_intent(text, session_id="logs-session") is None
    assert not is_global_verification_query(text, session_id="logs-session")


def test_compose_logs_for_both_services(health_rows):
    _seed_health_context("logs-session", health_rows)

    def _fake_fetch(*, service_name: str, limit: int = 5, **kwargs):
        return {
            "ok": True,
            "logs": [
                {
                    "timestamp": "2026-05-29T12:00:00Z",
                    "level": "INFO",
                    "message": f"{service_name} started",
                    "source": "runtime_cli_logs",
                }
            ],
            "sources_checked": ["runtime_cli_logs"],
            "errors": [],
        }

    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        return_value={"railway_credential_ok": True, "railway_api_connection_ok": True, "inventory": {"ok": True, "projects": []}},
    ), patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
        return_value=(health_rows, None),
    ), patch(
        "aethos_core.providers.railway.operations.logs_multisource.fetch_railway_service_logs_fast",
        side_effect=_fake_fetch,
    ):
        from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn

        result = route_operational_conversation_kernel_turn(
            "give me top 5 logs for each",
            session_id="logs-session",
        )

    assert result is not None
    assert "aethos-api" in result.reply
    assert "aethos-ui" in result.reply
    assert "aethos-api started" in result.reply
    assert "aethos-ui started" in result.reply
    assert "No mutation has been performed." in result.reply


def test_killit_logs_do_not_match_railway_named_service_router(health_rows):
    _seed_health_context("logs-session", health_rows)
    killit_row = {
        "target_id": "dt-killit",
        "alias": "killit",
        "repo": "pilotmain/killit",
        "vercel_project": "killit",
        "default_provider": "vercel",
    }
    text = "give me top 5 logs for killit?"
    with patch(
        "aethos_core.deployment_targets.registry.match_aliases_in_text",
        return_value=killit_row,
    ):
        assert not is_railway_named_service_log_request(text, session_id="logs-session")


def test_log_reply_is_not_compressed_by_conversational_pacing():
    from aethos_core.conversation.polish_compat import compress_for_channel

    long_reply = "\n\n".join(
        [
            "Live Railway logs for **aethos-api, aethos-ui** (top **5** per service):",
            "### pilotos / staging / aethos-api",
            "Health: **healthy** · deployment: `success`",
            "**Latest 5 logs:**",
            "- `2026-05-29T12:00:00Z` **INFO** — api line 1",
            "- `2026-05-29T12:00:01Z` **INFO** — api line 2",
            "### pilotos / staging / aethos-ui",
            "Health: **healthy** · deployment: `success`",
            "**Latest 5 logs:**",
            "- `2026-05-29T12:00:02Z` **INFO** — ui line 1",
        ]
    )
    compressed = compress_for_channel(long_reply, channel="chat", max_paragraphs=5)
    assert "ui line 1" not in compressed

    from aethos_core.conversation.polish_compat import finalize_grounded_reply

    shaped = finalize_grounded_reply(
        long_reply,
        emotional_context={"channel": "chat", "session_id": "logs-session"},
        intent="railway_named_service_logs",
    )
    assert "ui line 1" in shaped
    assert "### pilotos / staging / aethos-ui" in shaped
