# SPDX-License-Identifier: Apache-2.0
"""Failed-service fix plan tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.failed_service_investigation.failed_service_router import compose_failed_service_investigation_reply
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    yield
    clear_provider_wide_health_for_tests()


def _seed_worker_report(session_id: str) -> None:
    row = {
        "service": "worker",
        "project": "talking-avatar-worker",
        "environment": "production",
        "status": "failed",
        "health": "failed",
        "deployment_state": "crashed",
        "service_id": "svc-worker",
    }
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={
            "services": [row],
            "counts": {"total": 1, "healthy": 0, "failed": 1, "unknown": 0},
            "failures": [row],
            "unknown": [],
        },
        summary={"total": 1, "healthy": 0, "failed": 1, "unknown": 0},
    )


def _mock_logs(*, ok: bool = True):
    return patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={
            "ok": ok,
            "logs": [] if not ok else [{"message": "process exited with code 1"}],
            "sources_checked": ["deployment_logs"] if ok else [],
            "errors": [] if ok else ["no logs"],
            "all_sources_failed": not ok,
        },
    )


def test_fix_plan_uses_cached_failed_service_context():
    _seed_worker_report("fix-plan")
    with _mock_logs():
        reply, intent, meta = compose_failed_service_investigation_reply(
            "create fix plan for talking-avatar-worker",
            session_id="fix-plan",
        )
    assert intent == "failed_service_fix_plan"
    assert meta["service"] == "worker"
    assert meta["project"] == "talking-avatar-worker"
    assert "Fix plan for" in reply
    assert "talking-avatar-worker" in reply


def test_no_mutation_without_approval():
    _seed_worker_report("fix-approval")
    with _mock_logs():
        reply, intent, meta = compose_failed_service_investigation_reply(
            "create fix plan for worker",
            session_id="fix-approval",
        )
    assert meta.get("requires_approval") == "true"
    assert "No mutation has been performed yet." in reply


def test_includes_evidence_gaps_when_logs_unavailable():
    _seed_worker_report("fix-gaps")
    with _mock_logs(ok=False):
        reply, intent, meta = compose_failed_service_investigation_reply(
            "create fix plan for talking-avatar-worker",
            session_id="fix-gaps",
        )
    assert intent == "failed_service_fix_plan"
    assert "Evidence gaps:" in reply
    assert "unavailable" in reply.lower()


def test_includes_provider_specific_next_checks():
    _seed_worker_report("fix-next")
    with _mock_logs(ok=False):
        reply, intent, meta = compose_failed_service_investigation_reply(
            "create fix plan for worker",
            session_id="fix-next",
        )
    assert "Evidence to check:" in reply
    assert "Fetch Railway deployment/runtime logs" in reply
    assert "Inspect Railway service events" in reply
    assert "Verify env/config" in reply
    assert "Do **not** restart/redeploy yet" in reply
