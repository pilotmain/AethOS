# SPDX-License-Identifier: Apache-2.0
"""Failed-service fallback discovery tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.operation_preflight_prompts import create_operation_preflight_job_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.failed_service_investigation.fallback_discovery import (
    cache_has_health_report,
    discover_provider_if_cache_missing,
    refresh_health_report_if_needed,
    resolve_failed_service_with_fallback,
)
from aethos_core.failed_service_investigation.failed_service_router import compose_failed_service_investigation_reply
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.operational_result_store import clear_operational_results_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_operational_results_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_operational_results_for_tests()


def _rows() -> list[dict]:
    return [
        {
            "service": "MongoDB",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "failed",
            "service_id": "svc-mongo",
        },
        {
            "service": "worker",
            "project": "talking-avatar-worker",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "crashed",
            "service_id": "svc-worker",
        },
    ]


def _mock_inventory():
    return patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
        return_value=(_rows(), None),
    )


def _mock_logs():
    return patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": ["unavailable"], "all_sources_failed": True},
    )


def test_cache_missing_inventory_resolves_mongodb():
    assert cache_has_health_report(session_id="fb-mongo") is False
    with _mock_inventory(), _mock_logs():
        reply, intent, meta = compose_failed_service_investigation_reply("why is MongoDB failed?", session_id="fb-mongo")
    assert intent == "failed_service_diagnosis"
    assert meta["service"] == "MongoDB"
    assert meta.get("fallback_discovery") == "true"
    assert "refresh Railway inventory" in reply
    assert "MongoDB" in reply
    assert create_operation_preflight_job_reply("why is MongoDB failed?", session_id="fb-mongo") is None


def test_cache_missing_resolves_talking_avatar_worker_fix_plan():
    with _mock_inventory(), _mock_logs():
        reply, intent, meta = compose_failed_service_investigation_reply(
            "create fix plan for talking-avatar-worker",
            session_id="fb-worker",
        )
    assert intent == "failed_service_fix_plan"
    assert meta["project"] == "talking-avatar-worker"
    assert meta["service"] == "worker"
    assert "refresh Railway inventory" in reply


def test_discovery_failure_asks_targeted_clarification():
    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
        return_value=([], "token missing"),
    ):
        resolution, discovery = resolve_failed_service_with_fallback("why is MongoDB failed?", session_id="fb-fail")
    assert resolution.reason == "discovery_failed"
    assert discovery.discovered is False


def test_refresh_health_report_populates_cache():
    assert cache_has_health_report(session_id="fb-refresh") is False
    with _mock_inventory():
        ok, _err = refresh_health_report_if_needed(session_id="fb-refresh")
    assert ok is True
    assert cache_has_health_report(session_id="fb-refresh") is True


def test_discover_provider_if_cache_missing():
    with _mock_inventory():
        result = discover_provider_if_cache_missing(session_id="fb-discover")
    assert result.discovered is True
    assert result.service_count == 2


def test_diagnosis_continues_after_fallback_discovery_via_chat():
    with _mock_inventory(), _mock_logs():
        result = resolve_chat_turn("why is MongoDB failed?", session_id="fb-chat", apply_relational_layer=False)
    assert result.intent == "failed_service_diagnosis"
    assert result.meta.get("fallback_discovery") == "true"
    assert "Classification:" in result.reply or "Insufficient evidence" in result.reply
