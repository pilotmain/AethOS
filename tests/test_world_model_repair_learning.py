# SPDX-License-Identifier: Apache-2.0
"""World model repair learning integration tests."""

from __future__ import annotations

import pytest

from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
from aethos_core.operation_lifecycle.operation_state_store import reset_operation_state_store_for_tests
from aethos_core.post_mutation_verification.verification_reply_composer import build_verification_bundle
from aethos_core.repair_memory.repair_attempt_memory import reset_repair_memory_for_tests
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store
from aethos_core.world_model.hypothesis_graph import Hypothesis
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.world_state_store import clear_world_model_for_tests, load_investigation_state, save_investigation_state


@pytest.fixture(autouse=True)
def _clean():
    reset_operation_state_store_for_tests()
    reset_repair_memory_for_tests()
    clear_world_model_for_tests()
    reset_global_lifecycle_index_for_tests()
    yield
    reset_operation_state_store_for_tests()
    reset_repair_memory_for_tests()
    clear_world_model_for_tests()
    reset_global_lifecycle_index_for_tests()


def _seed_failed_restart_verification(session_id: str) -> str:
    target = "pilotcore-sales-engine / production / MongoDB"
    state = InvestigationState(
        target=target,
        session_id=session_id,
        service="MongoDB",
        project="pilotcore-sales-engine",
        environment="production",
        confidence_score=0.72,
        confidence_label="moderate",
        active_investigation=True,
        evidence=["failed_runtime_status"],
        hypotheses=[
            Hypothesis(type="restart_recovery", confidence=0.7, label="Restart may recover MongoDB"),
        ],
        next_best_action="Restart MongoDB after confirming surrounding evidence.",
        next_best_action_key="restart_after_evidence",
    )
    save_investigation_state(state)

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
            "preflight_match_key": "railway:restart:mongodb",
            "mutation_execution_approved": True,
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
    return target


def test_repair_attempt_added_to_investigation_state() -> None:
    session_id = "wm-repair-attempt"
    target = _seed_failed_restart_verification(session_id)

    state = load_investigation_state(session_id=session_id, target=target)
    assert state is not None
    attempts = state.meta.get("repair_attempts") or []
    assert len(attempts) >= 1
    assert attempts[0]["operation"] == "restart"
    assert attempts[0]["helped"] is False
    assert "restart" in state.meta.get("failed_actions", [])


def test_failed_action_reduces_restart_recommendation_confidence() -> None:
    session_id = "wm-repair-confidence"
    target = _seed_failed_restart_verification(session_id)

    state = load_investigation_state(session_id=session_id, target=target)
    assert state is not None
    restart_hypothesis = next(h for h in state.hypotheses if "restart" in h.label.lower())
    assert restart_hypothesis.confidence <= 0.35
    assert restart_hypothesis.status == "weakened"
    assert state.confidence_score <= 0.6


def test_next_best_action_changes_to_deeper_evidence_inspection() -> None:
    session_id = "wm-repair-next-action"
    target = _seed_failed_restart_verification(session_id)

    state = load_investigation_state(session_id=session_id, target=target)
    assert state is not None
    assert state.next_best_action_key == "deeper_evidence_inspection"
    assert "fetch full failure-window logs" in state.next_best_action
    assert "restart_did_not_resolve" in state.evidence
    assert "failed_restart_attempt" in state.evidence
