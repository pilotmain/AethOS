# SPDX-License-Identifier: Apache-2.0
"""Pending verification continuation tests."""

from __future__ import annotations

import pytest

from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import (
    reset_operation_state_store_for_tests,
    upsert_operation_state_from_job,
)
from aethos_core.operations.mutations.lifecycle_authority import EXECUTION_COMPLETED_STATE
from aethos_core.post_mutation_verification.verification_intent_router import (
    reset_pending_verification_for_tests,
    route_post_mutation_verification,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    reset_operation_state_store_for_tests()
    reset_global_lifecycle_index_for_tests()
    reset_pending_verification_for_tests()
    yield
    reset_operation_state_store_for_tests()
    reset_global_lifecycle_index_for_tests()
    reset_pending_verification_for_tests()


def _seed_execution_job(*, session_id: str = "session-a", service: str = "MongoDB", suffix: str = "a") -> str:
    pf = authority.create_job(
        title=f"Restart {service}",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": service,
            "target": {
                "service_name": service,
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
            },
            "preflight_status": "ready_for_mutation_approval",
            "preflight_match_key": f"railway:restart:{service.lower()}",
            "mutation_execution_approved": True,
            "is_current": True,
        },
        session_id=session_id,
        auto_run=False,
    )
    exec_job = authority.create_job(
        title=f"Restart {service} execution",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": service,
            "target": {
                "service_name": service,
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
            "railway_before_snapshot": {"latest_deployment_status": "failed"},
            "railway_after_snapshot": {"latest_deployment_status": "failed"},
            "restart_service_health": "failed",
            "canonical_lifecycle_state": EXECUTION_COMPLETED_STATE,
            "lifecycle_summary": f"Mutation restart on {service}",
            "preflight_match_key": f"railway:restart:{service.lower()}",
            "provider_evidence_bundle": {"log_summary": "wiredtiger startup activity"},
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
    job = job_store.get(exec_job.id)
    if job:
        job.updated_at = float(hash(suffix) % 1000)
    upsert_operation_state_from_job(job)
    return exec_job.id


def test_fetch_logs_target_path_continues_fetch_logs() -> None:
    _seed_execution_job(service="MongoDB", suffix="mongo")
    _seed_execution_job(service="pilotos-api", suffix="api")
    first = route_post_mutation_verification("fetch logs after restart", session_id="fresh")
    assert first is not None
    assert first[1] == "post_mutation_verification_disambiguation"

    continued = route_post_mutation_verification(
        "pilotcore-sales-engine/production/MongoDB",
        session_id="fresh",
    )
    assert continued is not None
    assert continued[1] == "post_mutation_fetch_logs"
    assert "Fetching logs after the latest" in continued[0]
    assert "What would you like to do?" not in continued[0]


def test_verify_health_option_number_continues_verification() -> None:
    _seed_execution_job(service="MongoDB", suffix="mongo")
    _seed_execution_job(service="pilotos-api", suffix="api")
    first = route_post_mutation_verification("verify health", session_id="fresh")
    assert first is not None
    assert first[1] == "post_mutation_verification_disambiguation"

    continued = route_post_mutation_verification("1", session_id="fresh")
    assert continued is not None
    assert continued[1] == "post_mutation_verify_health"
    assert "latest mutation I found" in continued[0]


def test_copied_list_item_continues_pending_intent() -> None:
    _seed_execution_job(service="MongoDB", suffix="mongo")
    _seed_execution_job(service="pilotos-api", suffix="api")
    route_post_mutation_verification("fetch logs after restart", session_id="fresh")
    continued = route_post_mutation_verification(
        "2. pilotcore-sales-engine / production / pilotos-api — restart",
        session_id="fresh",
    )
    assert continued is not None
    assert continued[1] == "post_mutation_fetch_logs"
    assert "pilotos-api" in continued[0]


def test_bare_target_with_no_pending_intent_shows_menu() -> None:
    _seed_execution_job()
    reply = route_post_mutation_verification(
        "pilotcore-sales-engine/production/MongoDB",
        session_id="fresh",
    )
    assert reply is not None
    assert reply[1] == "post_mutation_target_lifecycle_menu"
    assert "What would you like to do?" in reply[0]
