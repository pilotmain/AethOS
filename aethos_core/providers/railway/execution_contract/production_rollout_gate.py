# SPDX-License-Identifier: Apache-2.0
"""FIX 121 — rollout stage gates, health checkpoints, approval boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.production_policy import (
    assess_railway_production_policy,
    is_production_shadow_execution_enabled,
)
from aethos_core.providers.railway.execution_contract.production_rollout_orchestration_contract import (
    AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED,
    BLAST_RADIUS_BY_STAGE,
    ROLLOUT_ADVANCE_APPROVAL_PHRASE,
    ROLLOUT_STAGES,
    RolloutStage,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    load_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    load_verification_receipt,
)


def _extract_rollout_advance_approval(text: str) -> bool:
    return ROLLOUT_ADVANCE_APPROVAL_PHRASE in (text or "")


def _load_rollout_orchestration_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "railway_production_rollout_orchestration_enabled", True)),
        "require_verification_for_advance": bool(
            getattr(settings, "railway_production_rollout_require_verification", True)
        ),
        "require_escalation_clear_for_advance": bool(
            getattr(settings, "railway_production_rollout_require_escalation_clear", True)
        ),
    }


@dataclass(frozen=True)
class RolloutHealthCheckpoint:
    checkpoint_id: str
    passed: bool
    detail: str
    evidence_present: bool


@dataclass(frozen=True)
class RolloutStageGateResult:
    stage: str
    ready_to_advance: bool
    rollout_paused: bool
    autonomous_promotion_permitted: bool
    blast_radius: str
    health_checkpoints: list[RolloutHealthCheckpoint] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "ready_to_advance": self.ready_to_advance,
            "rollout_paused": self.rollout_paused,
            "autonomous_promotion_permitted": self.autonomous_promotion_permitted,
            "blast_radius": self.blast_radius,
            "health_checkpoints": [
                {
                    "checkpoint_id": c.checkpoint_id,
                    "passed": c.passed,
                    "detail": c.detail,
                    "evidence_present": c.evidence_present,
                }
                for c in self.health_checkpoints
            ],
            "blockers": list(self.blockers),
            "messages": list(self.messages),
        }


def _stage_index(stage: str) -> int:
    try:
        return ROLLOUT_STAGES.index(stage)  # type: ignore[arg-type]
    except ValueError:
        return -1


def _escalation_blocks_rollout(*, execution_id: str) -> tuple[bool, str]:
    from aethos_core.providers.railway.execution_contract.production_rollback_escalation import (
        assess_rollback_escalation_gate,
        load_rollback_escalation_config,
    )
    from aethos_core.providers.railway.execution_contract.production_rollback_escalation_store import (
        load_escalation,
    )

    if not load_rollback_escalation_config()["enabled"]:
        return False, ""
    record = load_escalation(execution_id=execution_id)
    if not record:
        return False, ""
    recommendation = str(record.get("rollback_recommendation") or "none")
    state = str(record.get("decision_state") or "")
    if recommendation in ("none", "blocked_pending_evidence"):
        return False, ""
    if state in {"escalation_closed", "human_declined_rollback", "shadow_rehearsal_completed"}:
        return False, ""
    gate = assess_rollback_escalation_gate(execution_id=execution_id)
    if gate.decision_state in {"human_declined_rollback", "escalation_closed"}:
        return False, ""
    return True, f"rollback_escalation_active:{recommendation}"


def assess_rollout_health_checkpoints(
    *,
    execution_id: str,
    stage: RolloutStage,
    plan: dict[str, Any] | None = None,
) -> list[RolloutHealthCheckpoint]:
    plan = plan or {}
    shadow = load_shadow_journal(execution_id=execution_id) or {}
    verification = load_verification_receipt(execution_id=execution_id) or {}
    assessment = verification.get("assessment") or {}

    checkpoints: list[RolloutHealthCheckpoint] = []

    checkpoints.append(
        RolloutHealthCheckpoint(
            checkpoint_id="shadow_forward_complete",
            passed=bool(shadow.get("forward_shadow_completed")),
            detail="FIX 118 shadow forward rehearsal",
            evidence_present=bool(shadow.get("forward_shadow_completed")),
        )
    )
    checkpoints.append(
        RolloutHealthCheckpoint(
            checkpoint_id="verification_evidence",
            passed=bool(assessment.get("verification_passed")),
            detail="FIX 119 multi-signal verification",
            evidence_present=bool(verification.get("evidence")),
        )
    )
    checkpoints.append(
        RolloutHealthCheckpoint(
            checkpoint_id="operator_quorum",
            passed=bool(
                assess_railway_production_policy(plan=plan, execution_id=execution_id).operator_quorum_satisfied
            ),
            detail="FIX 117 operator quorum",
            evidence_present=True,
        )
    )

    if stage == "shadow":
        return checkpoints

    checkpoints.append(
        RolloutHealthCheckpoint(
            checkpoint_id="shadow_stage_completed",
            passed=str((load_rollout_journal_stage_status(execution_id, "shadow"))) == "completed",
            detail="Rollout shadow stage marked complete",
            evidence_present=True,
        )
    )
    if stage in ("staged_rollout", "full_rollout"):
        checkpoints.append(
            RolloutHealthCheckpoint(
                checkpoint_id="canary_stage_completed",
                passed=str(load_rollout_journal_stage_status(execution_id, "canary")) == "completed",
                detail="Rollout canary stage marked complete",
                evidence_present=True,
            )
        )
    if stage == "full_rollout":
        checkpoints.append(
            RolloutHealthCheckpoint(
                checkpoint_id="staged_rollout_completed",
                passed=str(load_rollout_journal_stage_status(execution_id, "staged_rollout"))
                == "completed",
                detail="Rollout staged expansion marked complete",
                evidence_present=True,
            )
        )
    return checkpoints


def load_rollout_journal_stage_status(execution_id: str, stage: str) -> str:
    from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
        load_rollout_journal,
    )

    journal = load_rollout_journal(execution_id=execution_id) or {}
    statuses = journal.get("stage_status") or {}
    return str(statuses.get(stage) or "pending")


def assess_rollout_stage_gate(
    *,
    execution_id: str,
    stage: RolloutStage,
    plan: dict[str, Any] | None = None,
    user_text: str = "",
    journal: dict[str, Any] | None = None,
    require_advance_phrase: bool = False,
) -> RolloutStageGateResult:
    from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
        load_rollout_journal,
    )

    plan = plan or {}
    journal = journal or load_rollout_journal(execution_id=execution_id) or {}
    cfg = _load_rollout_orchestration_config()
    blockers: list[str] = []
    messages: list[str] = []

    if not cfg["enabled"]:
        blockers.append("rollout_orchestration_disabled")
        messages.append("Production rollout orchestration is disabled.")

    if journal.get("rollout_paused"):
        blockers.append("rollout_paused")

    if not is_production_shadow_execution_enabled():
        blockers.append("production_shadow_execution_disabled")

    from aethos_core.providers.railway.execution_contract.production_incident_command import (
        incident_blocks_rollout_advance,
    )

    policy = assess_railway_production_policy(plan=plan, execution_id=execution_id, journal=journal)
    inc_blocks, inc_detail = incident_blocks_rollout_advance(execution_id=execution_id)
    if inc_blocks:
        blockers.append(inc_detail)
        messages.append("Resolve or close the production incident before rollout advance.")
    if policy.incident_mode_active and "production_incident_mode_active" not in blockers:
        blockers.append("production_incident_mode_active")
    if policy.deployment_freeze_active:
        blockers.append("production_deployment_freeze_active")
    if policy.forward_live_permitted:
        blockers.append("production_forward_live_must_remain_locked")

    checkpoints = assess_rollout_health_checkpoints(
        execution_id=execution_id,
        stage=stage,
        plan=plan,
    )
    for cp in checkpoints:
        if not cp.passed and cp.checkpoint_id in {
            "shadow_forward_complete",
            "verification_evidence",
            "operator_quorum",
        }:
            blockers.append(f"health_checkpoint_failed:{cp.checkpoint_id}")

    if cfg["require_escalation_clear_for_advance"]:
        esc_blocks, esc_detail = _escalation_blocks_rollout(execution_id=execution_id)
        if esc_blocks:
            blockers.append("rollback_escalation_blocking_rollout")
            messages.append(f"Resolve rollback escalation before rollout advance ({esc_detail}).")

    if cfg["require_verification_for_advance"]:
        verification = load_verification_receipt(execution_id=execution_id) or {}
        if not (verification.get("assessment") or {}).get("verification_passed"):
            blockers.append("verification_evidence_required")
            messages.append("Production verification must pass before rollout advance.")

    current = str(journal.get("current_stage") or ROLLOUT_STAGES[0])
    if _stage_index(stage) > _stage_index(current) + 1:
        blockers.append("rollout_stage_skip_forbidden")
        messages.append("Advance one governed stage at a time.")

    if stage != current and _stage_index(stage) == _stage_index(current) + 1:
        pass
    elif stage == current:
        statuses = journal.get("stage_status") or {}
        if statuses.get(stage) == "completed":
            blockers.append("rollout_stage_already_completed")

    if require_advance_phrase and not _extract_rollout_advance_approval(user_text):
        blockers.append("rollout_advance_approval_required")
        messages.append(f"Advance phrase required: {ROLLOUT_ADVANCE_APPROVAL_PHRASE}")

    from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy import (
        policy_blockers_for_rollout_advance,
    )

    for code in policy_blockers_for_rollout_advance(
        execution_id=execution_id,
        rollout_stage=stage,
        plan=plan,
    ):
        if code not in blockers:
            blockers.append(code)

    blockers.append("autonomous_rollout_promotion_prohibited")
    messages.append("Autonomous promotion is never permitted — human approval per stage.")

    ready = not any(b for b in blockers if b != "autonomous_rollout_promotion_prohibited")

    return RolloutStageGateResult(
        stage=stage,
        ready_to_advance=ready,
        rollout_paused=bool(journal.get("rollout_paused")),
        autonomous_promotion_permitted=AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED,
        blast_radius=BLAST_RADIUS_BY_STAGE.get(stage, "local"),
        health_checkpoints=checkpoints,
        blockers=blockers,
        messages=messages,
    )
