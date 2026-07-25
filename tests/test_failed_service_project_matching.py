# SPDX-License-Identifier: Apache-2.0
"""Failed-service project and service name matching tests."""

from __future__ import annotations

import pytest

from aethos_core.failed_service_investigation.failed_service_resolver import (
    matches_failed_service_from_cache,
    resolve_failed_service_target,
)
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    yield
    clear_provider_wide_health_for_tests()


def _worker_row() -> dict:
    return {
        "service": "worker",
        "project": "talking-avatar-worker",
        "environment": "production",
        "status": "failed",
        "health": "failed",
        "deployment_state": "crashed",
        "service_id": "svc-worker",
    }


def _mongo_row() -> dict:
    return {
        "service": "MongoDB",
        "project": "pilotcore-sales-engine",
        "environment": "production",
        "status": "failed",
        "health": "failed",
        "deployment_state": "failed",
        "service_id": "svc-mongo",
    }


def _seed(session_id: str, rows: list[dict]) -> None:
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={
            "services": rows,
            "counts": {"total": len(rows), "healthy": 0, "failed": len(rows), "unknown": 0},
            "failures": rows,
            "unknown": [],
        },
        summary={"total": len(rows), "healthy": 0, "failed": len(rows), "unknown": 0},
    )


def test_project_name_match_talking_avatar_worker():
    _seed("match-project", [_worker_row()])
    assert matches_failed_service_from_cache("create fix plan for talking-avatar-worker", session_id="match-project")
    resolution = resolve_failed_service_target(
        "create fix plan for talking-avatar-worker",
        session_id="match-project",
    )
    assert resolution.ok is True
    assert resolution.target is not None
    assert resolution.target.row["service"] == "worker"


def test_service_name_match_mongodb():
    _seed("match-service", [_mongo_row()])
    assert matches_failed_service_from_cache("why is MongoDB failed?", session_id="match-service")
    resolution = resolve_failed_service_target("why is MongoDB failed?", session_id="match-service")
    assert resolution.ok is True
    assert resolution.target is not None
    assert resolution.target.row["service"] == "MongoDB"


def test_combined_project_service_match():
    _seed("match-combined", [_worker_row()])
    resolution = resolve_failed_service_target(
        "check logs for talking-avatar-worker worker",
        session_id="match-combined",
    )
    assert resolution.ok is True
    assert resolution.target is not None
    assert resolution.target.row["project"] == "talking-avatar-worker"


def test_duplicate_matches_ask_clarification():
    rows = [
        {"service": "api", "project": "alpha", "environment": "production", "status": "failed", "health": "failed"},
        {"service": "api", "project": "beta", "environment": "production", "status": "failed", "health": "failed"},
    ]
    _seed("match-dup", rows)
    resolution = resolve_failed_service_target("why is api failed?", session_id="match-dup")
    assert resolution.ok is False
    assert resolution.reason == "ambiguous_service"
    assert len(resolution.candidates or []) == 2
