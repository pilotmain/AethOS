# SPDX-License-Identifier: Apache-2.0
"""Global mutation lifecycle index tests."""

from __future__ import annotations

import pytest

from aethos_core.operation_lifecycle.global_lifecycle_index import (
    find_latest_mutation_any_session,
    find_latest_mutation_by_target,
    find_recent_mutations,
    index_mutation_lifecycle,
    rebuild_global_lifecycle_index_from_jobs,
    reset_global_lifecycle_index_for_tests,
)
from aethos_core.operation_lifecycle.operation_state_store import (
    OperationLifecycleState,
    reset_operation_state_store_for_tests,
    upsert_operation_state_from_job,
)
from aethos_core.operations.mutations.lifecycle_authority import EXECUTION_COMPLETED_STATE
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    reset_operation_state_store_for_tests()
    reset_global_lifecycle_index_for_tests()
    yield
    reset_operation_state_store_for_tests()
    reset_global_lifecycle_index_for_tests()


def _seed_execution_job(*, session_id: str = "default") -> str:
    pf = authority.create_job(
        title="Restart MongoDB",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "MongoDB",
            "target": {
                "service_name": "MongoDB",
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
            },
            "preflight_status": "ready_for_mutation_approval",
            "preflight_match_key": "railway:restart:mongodb",
            "mutation_execution_approved": True,
            "is_current": True,
        },
        session_id=session_id,
        auto_run=False,
    )
    exec_job = authority.create_job(
        title="Restart MongoDB execution",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "MongoDB",
            "target": {
                "service_name": "MongoDB",
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
            },
            "preflight_job_id": pf.id,
            "executed": True,
            "execution_state": "execution_completed",
            "verification_state": "verification_running",
            "restart_verification_state": "stabilizing",
            "restart_command_submitted": True,
            "provider_result": {"restart_command_submitted": True, "ok": True},
            "canonical_lifecycle_state": EXECUTION_COMPLETED_STATE,
            "lifecycle_summary": "Mutation restart on MongoDB · restart requested · stabilizing",
            "preflight_match_key": "railway:restart:mongodb",
        },
        session_id=session_id,
        auto_run=False,
    )
    job_store.complete_with_result(
        exec_job.id,
        full_result="done",
        summary="done",
        preview="done",
        provider="mutation_execution",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )
    upsert_operation_state_from_job(job_store.get(exec_job.id))
    return exec_job.id


def test_execution_completion_writes_global_index() -> None:
    _seed_execution_job(session_id="session-a")
    latest = find_latest_mutation_any_session()
    assert latest is not None
    assert latest.service == "MongoDB"
    assert latest.execution_job_id


def test_lookup_latest_mutation_any_session() -> None:
    _seed_execution_job(session_id="session-a")
    latest = find_latest_mutation_any_session(provider="railway", operation="restart")
    assert latest is not None
    assert latest.project == "pilotcore-sales-engine"


def test_lookup_by_target() -> None:
    _seed_execution_job(session_id="session-a")
    found = find_latest_mutation_by_target(
        provider="railway",
        project="pilotcore-sales-engine",
        environment="production",
        service="MongoDB",
    )
    assert found is not None
    assert found.execution_status == "completed"


def test_lookup_after_session_reset() -> None:
    _seed_execution_job(session_id="session-a")
    reset_operation_state_store_for_tests()
    found = find_latest_mutation_by_target(
        provider="railway",
        project="pilotcore-sales-engine",
        environment="production",
        service="MongoDB",
    )
    assert found is not None
    assert found.session_id == "session-a"


def test_rebuild_from_jobs() -> None:
    job_id = _seed_execution_job(session_id="session-a")
    reset_global_lifecycle_index_for_tests()
    assert find_latest_mutation_any_session() is None
    count = rebuild_global_lifecycle_index_from_jobs()
    assert count >= 1
    latest = find_latest_mutation_any_session()
    assert latest is not None
    assert latest.execution_job_id == job_id


def test_find_recent_mutations() -> None:
    _seed_execution_job(session_id="session-a")
    rows = find_recent_mutations(limit=3)
    assert len(rows) == 1
    assert rows[0].service == "MongoDB"


def test_index_mutation_lifecycle_direct() -> None:
    state = OperationLifecycleState(
        provider="railway",
        project="pilotcore-sales-engine",
        environment="production",
        service="MongoDB",
        operation="restart",
        execution_job_id="job-test123",
        execution_status="completed",
        session_id="tg-1-2",
        match_key="railway:restart:mongodb",
    )
    index_mutation_lifecycle(
        state,
        execution_params={"executed": True, "restart_command_submitted": True},
    )
    found = find_latest_mutation_by_target(
        provider="railway",
        project="pilotcore-sales-engine",
        environment="production",
        service="MongoDB",
    )
    assert found is not None
    assert found.execution_job_id == "job-test123"
