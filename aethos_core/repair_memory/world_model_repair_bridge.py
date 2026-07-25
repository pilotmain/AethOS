# SPDX-License-Identifier: Apache-2.0
"""Sync repair learning into world-model investigation state."""

from __future__ import annotations

from typing import Any

from aethos_core.post_mutation_verification.verification_context import VerificationContext
from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome
from aethos_core.repair_memory.recommendation_guard import _DEEPER_EVIDENCE_ACTION
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row


def sync_repair_learning_to_world_model(
    *,
    session_id: str,
    ctx: VerificationContext,
    outcome: RepairAttemptOutcome,
) -> InvestigationState | None:
    target = ctx.target_path
    if not target:
        return None

    state = _load_or_create_state(session_id=session_id, ctx=ctx, target=target)
    if state is None:
        return None

    attempts = list(state.meta.get("repair_attempts") or [])
    attempts = [row for row in attempts if row.get("execution_job_id") != outcome.execution_job_id]
    attempts.insert(0, outcome.to_dict())
    state.meta["repair_attempts"] = attempts[:10]

    failed_actions = list(state.meta.get("failed_actions") or [])
    if not outcome.helped and outcome.operation not in failed_actions:
        failed_actions.append(outcome.operation)
    state.meta["failed_actions"] = failed_actions

    if not outcome.helped:
        for tag in ("failed_restart_attempt", "restart_did_not_resolve"):
            if tag not in state.evidence:
                state.evidence.append(tag)
        state.next_best_action = _DEEPER_EVIDENCE_ACTION
        state.next_best_action_key = "deeper_evidence_inspection"
        state.conclusion = outcome.lesson
        for hypothesis in state.hypotheses:
            if "restart" in hypothesis.type.lower() or "restart" in hypothesis.label.lower():
                hypothesis.confidence = max(0.05, hypothesis.confidence * 0.5)
                hypothesis.status = "weakened"
        if state.confidence_score > 0.35:
            state.confidence_score = max(0.35, state.confidence_score - 0.15)
            state.confidence_label = "bounded" if state.confidence_score < 0.6 else state.confidence_label
    else:
        if "restart_recovery_verified" not in state.evidence:
            state.evidence.append("restart_recovery_verified")
        state.conclusion = outcome.lesson

    state.timeline.append(
        {
            "kind": "repair_learning",
            "operation": outcome.operation,
            "result": outcome.result,
            "helped": outcome.helped,
            "lesson": outcome.lesson,
        }
    )

    try:
        from aethos_core.world_model.world_state_store import save_investigation_state

        save_investigation_state(state)
    except Exception:
        pass
    return state


def _load_or_create_state(
    *,
    session_id: str,
    ctx: VerificationContext,
    target: str,
) -> InvestigationState | None:
    try:
        from aethos_core.world_model.world_state_store import load_investigation_state, save_investigation_state

        state = load_investigation_state(session_id=session_id, target=target)
        if state is not None:
            return state
    except Exception:
        state = None

    row = {
        "service": ctx.service or "",
        "project": ctx.lifecycle.project or "",
        "environment": ctx.lifecycle.environment or "",
        "provider": ctx.provider or "railway",
    }
    state = InvestigationState(
        target=target or target_label_from_row(row),
        session_id=session_id,
        provider=ctx.provider or "railway",
        service=ctx.service or "",
        project=ctx.lifecycle.project or "",
        environment=ctx.lifecycle.environment or "",
        active_investigation=True,
        evidence=["failed_runtime_status"] if not ctx.service_health.startswith("health") else [],
        missing_evidence=[
            "recent service events / exit code",
            "logs around the actual failure window",
            "storage/volume health",
        ],
        next_best_action=_DEEPER_EVIDENCE_ACTION,
        next_best_action_key="deeper_evidence_inspection",
        confidence_score=0.42,
        confidence_label="bounded",
    )
    try:
        from aethos_core.world_model.world_state_store import save_investigation_state

        save_investigation_state(state)
    except Exception:
        pass
    return state
