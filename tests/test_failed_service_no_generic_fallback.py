# SPDX-License-Identifier: Apache-2.0
"""Ensure cached failed-service rows never fall back to generic paths."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.aethos_identity.continuity_decision import compose_continuity_operational_reply
from aethos_core.chat.operation_preflight_prompts import create_operation_preflight_job_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.chat.vercel_readonly_prompts import create_vercel_readonly_job_reply
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    yield
    clear_provider_wide_health_for_tests()


def _seed(session_id: str) -> None:
    row = {
        "service": "MongoDB",
        "project": "pilotcore-sales-engine",
        "environment": "production",
        "status": "failed",
        "health": "failed",
        "deployment_state": "failed",
        "service_id": "svc-mongo",
    }
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": [row], "counts": {"total": 1, "failed": 1}, "failures": [row], "unknown": []},
        summary={"total": 1, "failed": 1},
    )


def _mock_logs():
    return patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": [], "all_sources_failed": True},
    )


def test_no_vercel_preflight_for_cached_failed_row():
    _seed("nogeneric-vercel")
    assert create_operation_preflight_job_reply("why is MongoDB failed?", session_id="nogeneric-vercel") is None
    assert create_vercel_readonly_job_reply("why is MongoDB failed?", session_id="nogeneric-vercel") is None


def test_no_generic_reconstruct_for_cached_failed_row():
    _seed("nogeneric-reconstruct")
    with _mock_logs():
        continuity = compose_continuity_operational_reply("why is MongoDB failed?", session_id="nogeneric-reconstruct")
    assert continuity is None


def test_no_llm_filler_for_cached_failed_row():
    _seed("nogeneric-llm")
    with _mock_logs(), patch("aethos_core.chat.service.complete_chat") as mock_complete:
        mock_complete.return_value = type("R", (), {"text": "generic filler", "used_llm": True, "provider": "x", "model": "y"})()
        result = resolve_chat_turn("why is MongoDB failed?", session_id="nogeneric-llm", apply_relational_layer=False)
    assert result.used_llm is False
    assert result.intent == "failed_service_diagnosis"
    assert "MongoDB" in result.reply
    mock_complete.assert_not_called()
