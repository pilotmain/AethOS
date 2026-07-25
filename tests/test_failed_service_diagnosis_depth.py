# SPDX-License-Identifier: Apache-2.0
"""Failed-service diagnosis depth tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.failed_service_investigation.failed_service_diagnosis import compose_diagnosis_reply
from aethos_core.failed_service_investigation.failed_service_fix_plan import compose_fix_plan_reply
from aethos_core.failed_service_investigation.failed_service_resolver import ResolvedFailedService
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests


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


def _worker_target() -> ResolvedFailedService:
    return ResolvedFailedService(
        row={
            "service": "worker",
            "project": "talking-avatar-worker",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "crashed",
            "service_id": "svc-worker",
        }
    )


def test_mongodb_wiredtiger_only_gives_bounded_diagnosis():
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={
            "ok": True,
            "logs": [{"timestamp": "2026-05-25T11:55:00+00:00", "message": "WiredTiger message"}, {"message": "WiredTiger recovery checkpoint"}],
            "sources_checked": ["deployment_logs"],
            "errors": [],
        },
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={
            "ok": True,
            "events": [{"created_at": "2026-04-01T10:00:00+00:00", "state": "FAILED", "message": "Deployment dep-old state=FAILED"}],
        },
    ):
        evidence = __import__(
            "aethos_core.failed_service_investigation.failed_service_diagnosis",
            fromlist=["collect_failed_service_evidence"],
        ).collect_failed_service_evidence(_mongo_target())
        body = compose_diagnosis_reply(evidence)

    assert "database_startup_or_storage_activity" in body or "Database startup or storage activity" in body
    assert "WiredTiger" in body
    assert "bounded" in body.lower() or "not claim a final root cause" in body
    assert "Evidence correlation:" in body
    assert "Best next step:" in body
    assert "Refresh Railway service events" in body
    assert "No mutation recommended yet." in body


def test_worker_crash_loop_diagnosis():
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={
            "ok": True,
            "logs": [{"timestamp": "2026-05-25T11:55:00+00:00", "message": "process exited with code 137"}, {"message": "container restart"}],
            "sources_checked": ["deployment_logs"],
            "errors": [],
        },
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": True, "events": [{"created_at": "2026-05-25T11:50:00+00:00", "state": "FAILED"}]},
    ):
        evidence = __import__(
            "aethos_core.failed_service_investigation.failed_service_diagnosis",
            fromlist=["collect_failed_service_evidence"],
        ).collect_failed_service_evidence(_worker_target())
        body = compose_diagnosis_reply(evidence)

    assert "Crash loop" in body
    assert "exit" in body.lower()


def test_fix_plan_includes_evidence_gaps_and_next_checks():
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={
            "ok": True,
            "logs": [{"timestamp": "2026-05-25T11:55:00+00:00", "message": "WiredTiger message"}],
            "sources_checked": ["deployment_logs"],
            "errors": [],
        },
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": True, "events": [{"created_at": "2026-04-01T10:00:00+00:00", "state": "FAILED"}]},
    ):
        body, plan = compose_fix_plan_reply(_mongo_target())

    assert "Evidence to check:" in body
    assert "Evidence gaps:" in body or "not strong enough" in body
    assert plan.get("proposed_operation") is None
    assert "No mutation has been performed yet." in body


def test_no_mutation_without_confidence():
    with patch(
        "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
        return_value={
            "ok": True,
            "logs": [{"timestamp": "2026-05-25T11:55:00+00:00", "message": "WiredTiger message"}],
            "sources_checked": ["deployment_logs"],
            "errors": [],
        },
    ), patch(
        "aethos_core.providers.railway.operations.service_events_api.get_service_events",
        return_value={"ok": True, "events": [{"created_at": "2026-04-01T10:00:00+00:00", "state": "FAILED"}]},
    ):
        body, plan = compose_fix_plan_reply(_worker_target())

    assert "Do **not** restart/redeploy yet" in body or plan.get("proposed_operation") is None
