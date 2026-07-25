# SPDX-License-Identifier: Apache-2.0
"""Lifecycle deduplication tests."""

from __future__ import annotations

import pytest

from aethos_core.operation_lifecycle.global_lifecycle_index import (
    dedupe_lifecycles_by_target_operation,
    find_latest_logical_mutation,
    index_mutation_lifecycle,
    reset_global_lifecycle_index_for_tests,
)
from aethos_core.operation_lifecycle.operation_state_store import OperationLifecycleState


@pytest.fixture(autouse=True)
def _clean():
    reset_global_lifecycle_index_for_tests()
    yield
    reset_global_lifecycle_index_for_tests()


def _state(
    *,
    service: str = "MongoDB",
    operation: str = "restart",
    job_id: str,
    updated_at: float,
    project: str = "pilotcore-sales-engine",
) -> OperationLifecycleState:
    return OperationLifecycleState(
        provider="railway",
        project=project,
        environment="production",
        service=service,
        operation=operation,
        execution_job_id=job_id,
        execution_status="completed",
        session_id="session-a",
        match_key=f"railway:{operation}:{service.lower()}",
        updated_at=updated_at,
    )


def test_three_mongodb_restarts_collapse_to_one_logical_candidate() -> None:
    for idx, job_id in enumerate(("job-a", "job-b", "job-c"), start=1):
        index_mutation_lifecycle(_state(job_id=job_id, updated_at=float(idx)))
    deduped = dedupe_lifecycles_by_target_operation(find_latest_logical_mutation(limit=10))
    assert len(deduped) == 1
    assert deduped[0].execution_job_id == "job-c"


def test_latest_execution_retained() -> None:
    index_mutation_lifecycle(_state(job_id="job-old", updated_at=1.0))
    index_mutation_lifecycle(_state(job_id="job-new", updated_at=99.0))
    latest = find_latest_logical_mutation(limit=1)[0]
    assert latest.execution_job_id == "job-new"


def test_multiple_targets_remain_separate() -> None:
    index_mutation_lifecycle(_state(service="MongoDB", job_id="job-mongo", updated_at=2.0))
    index_mutation_lifecycle(
        _state(
            service="pilotos-api",
            job_id="job-api",
            updated_at=3.0,
            project="pilotcore-sales-engine",
        )
    )
    deduped = dedupe_lifecycles_by_target_operation(find_latest_logical_mutation(limit=10))
    services = {row.service for row in deduped}
    assert services == {"MongoDB", "pilotos-api"}


def test_same_target_different_operations_remain_separate() -> None:
    index_mutation_lifecycle(_state(operation="restart", job_id="job-restart", updated_at=2.0))
    index_mutation_lifecycle(_state(operation="redeploy", job_id="job-redeploy", updated_at=3.0))
    deduped = dedupe_lifecycles_by_target_operation(find_latest_logical_mutation(limit=10))
    operations = {row.operation for row in deduped}
    assert operations == {"restart", "redeploy"}
