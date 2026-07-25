# SPDX-License-Identifier: Apache-2.0
"""Recommendation guard after failed restart tests."""

from __future__ import annotations

import pytest

from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import reset_operation_state_store_for_tests
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.post_mutation_verification.verification_followup_router import compose_post_mutation_verification_reply
from aethos_core.post_mutation_verification.verification_reply_composer import build_verification_bundle
from aethos_core.repair_memory.repair_attempt_memory import reset_repair_memory_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.world_model_followup_router import route_world_model_followup
from aethos_core.world_model.world_state_store import clear_world_model_for_tests, save_investigation_state


@pytest.fixture(autouse=True)
def _clean():
    reset_operation_state_store_for_tests()
    reset_repair_memory_for_tests()
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    reset_global_lifecycle_index_for_tests()
    yield
    reset_operation_state_store_for_tests()
    reset_repair_memory_for_tests()
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    reset_global_lifecycle_index_for_tests()


def _rows() -> list[dict]:
    return [
        {
            "service": "MongoDB",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "health": "failed",
        }
    ]


def _seed_health(session_id: str) -> None:
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload={"services": _rows(), "counts": {"total": 1, "failed": 1}, "failures": _rows(), "unknown": []},
        summary={"total": 1, "failed": 1},
    )


def _seed_state(session_id: str) -> InvestigationState:
    row = _rows()[0]
    state = InvestigationState(
        target=target_label_from_row(row),
        session_id=session_id,
        service="MongoDB",
        project="pilotcore-sales-engine",
        environment="production",
        confidence_score=0.55,
        confidence_label="bounded",
        active_investigation=True,
        evidence=["failed_runtime_status", "fresh_wiredtiger_logs", "stale_service_events"],
        next_best_action="Refresh Railway service events and fetch logs around the latest failed deployment window.",
    )
    save_investigation_state(state)
    return state


def _seed_failed_restart(session_id: str = "repair-guard") -> None:
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
            "verification_state": "verification_failed",
            "restart_verification_state": "verification_failed",
            "restart_command_submitted": True,
            "restart_service_health": "failed",
            "railway_before_snapshot": {"latest_deployment_status": "failed"},
            "railway_after_snapshot": {"latest_deployment_status": "failed"},
            "provider_result": {"restart_command_submitted": True, "ok": True},
            "provider_evidence_bundle": {"log_summary": "wiredtiger storage engine activity only"},
        },
        session_id=session_id,
        auto_run=False,
    )
    pf_job = job_store.get(pf.id)
    if pf_job:
        pf_job.params["mutation_execution_job_id"] = exec_job.id
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
    build_verification_bundle(session_id=session_id, text="verify health")


def test_what_should_we_do_next_does_not_recommend_restart_after_failed_restart() -> None:
    session_id = "repair-guard-next"
    _seed_health(session_id)
    _seed_state(session_id)
    _seed_failed_restart(session_id)

    reply, intent, _meta = route_world_model_followup("what should we do next?", session_id=session_id)
    if reply is None:
        from aethos_core.world_model.investigation_strategy_router import compose_investigation_strategy_route_reply

        routed = compose_investigation_strategy_route_reply("what should we do next?", session_id=session_id)
        assert routed is not None
        reply, intent, _meta = routed
    assert intent in {"world_model_next_action", "investigation_strategy_regressed"}
    assert "avoid another restart" in reply.lower() or "would not repeat the restart" in reply.lower()
    assert "fetch full logs" in reply.lower() or "fetch full failure-window logs" in reply.lower()


def test_should_we_restart_again_blocks_repeat_restart() -> None:
    session_id = "repair-guard-repeat"
    _seed_health(session_id)
    _seed_state(session_id)
    _seed_failed_restart(session_id)

    reply, intent, _meta = route_world_model_followup("should we restart again?", session_id=session_id)
    assert intent == "world_model_restart_safety"
    assert "No — not yet." in reply
    assert "already restarted" in reply.lower()
    assert "unlikely to help" in reply.lower()


def test_did_restart_help_returns_no_when_status_regressed() -> None:
    session_id = "repair-guard-help"
    _seed_failed_restart(session_id)

    reply = compose_post_mutation_verification_reply("did restart help?", session_id=session_id)
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "post_mutation_did_recover"
    assert "did not appear to help" in body.lower()
    assert "health: **failed**" in body
    assert "avoid another restart" in body.lower()
