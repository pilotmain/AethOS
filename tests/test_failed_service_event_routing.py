# SPDX-License-Identifier: Apache-2.0
"""Failed-service event routing tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.failed_service_investigation.failed_service_diagnosis import collect_failed_service_evidence, compose_events_reply
from aethos_core.failed_service_investigation.failed_service_resolver import ResolvedFailedService
from aethos_core.failed_service_investigation.global_preemption import route_failed_service_intent
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    yield
    clear_provider_wide_health_for_tests()


def _mongo_target() -> ResolvedFailedService:
    return ResolvedFailedService(
        row={
            "service": "MongoDB",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "failed",
            "service_id": "svc-mongo",
        }
    )


def _seed(session_id: str) -> None:
    row = _mongo_target().row
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": [row], "counts": {"total": 1, "failed": 1}, "failures": [row], "unknown": []},
        summary={"total": 1, "failed": 1},
    )


def test_inspect_events_calls_get_service_events():
    _seed("ev-route")
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": []},
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={
            "ok": True,
            "events": [{"id": "dep-1", "state": "FAILED", "created_at": "2026-01-01T00:00:00Z", "message": "Deployment dep-1 state=FAILED"}],
        },
    ) as events_mock:
        reply, intent, meta = route_failed_service_intent("inspect MongoDB service events", session_id="ev-route")
    assert intent == "failed_service_events"
    events_mock.assert_called_once()


def test_unavailable_events_returns_capability_gap():
    _seed("ev-gap")
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={"ok": False, "logs": [], "sources_checked": [], "errors": []},
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": False, "events": [], "capability_gap": True, "error": "Railway API token is not configured."},
    ):
        evidence = collect_failed_service_evidence(_mongo_target())
        body = compose_events_reply(evidence)
    assert "not available from the current adapter yet" in body
    assert "No mutation has been performed." in body


def test_event_output_included_in_diagnosis_context():
    _seed("ev-body")
    with patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={
            "ok": True,
            "events": [{"created_at": "2026-01-01T00:00:00Z", "state": "CRASHED", "message": "Deployment dep-9 state=CRASHED"}],
        },
    ):
        body = compose_events_reply({"target": _mongo_target().row, "target_label": "pilotcore-sales-engine / production / MongoDB", "status": "failed", "deployment_state": "failed"})
    assert "Events:" in body
    assert "CRASHED" in body
