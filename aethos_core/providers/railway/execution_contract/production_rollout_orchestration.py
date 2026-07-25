# SPDX-License-Identifier: Apache-2.0
"""FIX 121 — multi-stage production rollout orchestration (governed, no live mutations)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.production_rollout_gate import (
    RolloutStageGateResult,
    assess_rollout_health_checkpoints,
    assess_rollout_stage_gate,
)
from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
    get_or_create_rollout_journal,
    load_rollout_journal,
    save_rollout_journal,
)
from aethos_core.providers.railway.execution_contract.production_rollout_orchestration_contract import (
    AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED,
    BLAST_RADIUS_BY_STAGE,
    ROLLOUT_ADVANCE_APPROVAL_PHRASE,
    ROLLOUT_PAUSE_PHRASE,
    ROLLOUT_RESUME_PHRASE,
    ROLLOUT_STAGES,
    RolloutStage,
)
from aethos_core.providers.railway.execution_contract.production_rollout_receipts import (
    list_rollout_receipts,
    record_rollout_receipt,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    load_verification_receipt,
)

_STATUS_RX = re.compile(r"\bshow\s+railway\s+production\s+rollout\s+status\b", re.I)
_TIMELINE_RX = re.compile(r"\bshow\s+railway\s+production\s+rollout\s+timeline\b", re.I)
_CHECKPOINT_RX = re.compile(
    r"\bshow\s+railway\s+production\s+rollout\s+health\s+checkpoint\b",
    re.I,
)
_ADVANCE_RX = re.compile(r"\badvance\s+railway\s+production\s+rollout\b", re.I)
_PAUSE_RX = re.compile(r"\bpause\s+railway\s+production\s+rollout\b", re.I)
_RESUME_RX = re.compile(r"\bresume\s+railway\s+production\s+rollout\b", re.I)


@dataclass(frozen=True)
class RolloutOrchestrationResult:
    success: bool
    journal: dict[str, Any]
    action: str
    stage_advanced_to: str = ""
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def is_production_rollout_orchestration_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _STATUS_RX.search(raw)
        or _TIMELINE_RX.search(raw)
        or _CHECKPOINT_RX.search(raw)
        or _ADVANCE_RX.search(raw)
        or _PAUSE_RX.search(raw)
        or _RESUME_RX.search(raw)
    )


def extract_rollout_advance_approval(text: str) -> bool:
    return ROLLOUT_ADVANCE_APPROVAL_PHRASE in (text or "")


def extract_rollout_pause_approval(text: str) -> bool:
    return ROLLOUT_PAUSE_PHRASE in (text or "")


def extract_rollout_resume_approval(text: str) -> bool:
    return ROLLOUT_RESUME_PHRASE in (text or "")


def load_rollout_orchestration_config() -> dict[str, Any]:
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


def _next_stage(current: str) -> str | None:
    try:
        idx = ROLLOUT_STAGES.index(current)  # type: ignore[arg-type]
    except ValueError:
        return ROLLOUT_STAGES[0]
    if idx + 1 >= len(ROLLOUT_STAGES):
        return None
    return ROLLOUT_STAGES[idx + 1]


def build_rollout_status(
    *,
    execution_id: str,
    plan: dict[str, Any] | None = None,
    session_id: str = "",
) -> dict[str, Any]:
    journal, _ = get_or_create_rollout_journal(
        execution_id=execution_id,
        session_id=session_id,
        plan=plan,
    )
    current = str(journal.get("current_stage") or ROLLOUT_STAGES[0])
    gate = assess_rollout_stage_gate(
        execution_id=execution_id,
        stage=current,  # type: ignore[arg-type]
        plan=plan,
        journal=journal,
    )
    verification = load_verification_receipt(execution_id=execution_id)
    return {
        "journal": journal,
        "current_stage": current,
        "completed_stages": list(journal.get("completed_stages") or []),
        "orchestration_state": journal.get("orchestration_state"),
        "rollout_paused": journal.get("rollout_paused"),
        "blast_radius": journal.get("blast_radius"),
        "gate": gate.to_dict(),
        "verification_passed": bool((verification or {}).get("assessment", {}).get("verification_passed")),
        "receipt_count": len(list_rollout_receipts(execution_id=execution_id)),
        "autonomous_promotion_permitted": AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED,
    }


def pause_rollout(
    *,
    execution_id: str,
    user_text: str,
    plan: dict[str, Any] | None = None,
    session_id: str = "",
) -> RolloutOrchestrationResult:
    journal, _ = get_or_create_rollout_journal(
        execution_id=execution_id,
        session_id=session_id,
        plan=plan,
    )
    if not extract_rollout_pause_approval(user_text):
        return RolloutOrchestrationResult(
            success=False,
            journal=journal,
            action="pause_rejected",
            blockers=["rollout_pause_phrase_required"],
            detail=f"Pause phrase required: {ROLLOUT_PAUSE_PHRASE}",
        )
    journal["rollout_paused"] = True
    journal["paused_at_stage"] = str(journal.get("current_stage") or "")
    journal["orchestration_state"] = "paused"
    journal = save_rollout_journal(journal)
    record_rollout_receipt(
        execution_id=execution_id,
        stage=str(journal.get("paused_at_stage") or ""),
        action="rollout_paused",
        detail="Human-authorized rollout pause.",
    )
    return RolloutOrchestrationResult(
        success=True,
        journal=journal,
        action="rollout_paused",
        detail="Production rollout orchestration paused.",
    )


def resume_rollout(
    *,
    execution_id: str,
    user_text: str,
    plan: dict[str, Any] | None = None,
    session_id: str = "",
) -> RolloutOrchestrationResult:
    journal, _ = get_or_create_rollout_journal(
        execution_id=execution_id,
        session_id=session_id,
        plan=plan,
    )
    if not extract_rollout_resume_approval(user_text):
        return RolloutOrchestrationResult(
            success=False,
            journal=journal,
            action="resume_rejected",
            blockers=["rollout_resume_phrase_required"],
            detail=f"Resume phrase required: {ROLLOUT_RESUME_PHRASE}",
        )
    journal["rollout_paused"] = False
    journal["orchestration_state"] = "active"
    journal = save_rollout_journal(journal)
    record_rollout_receipt(
        execution_id=execution_id,
        stage=str(journal.get("current_stage") or ""),
        action="rollout_resumed",
        detail="Human-authorized rollout resume.",
    )
    return RolloutOrchestrationResult(
        success=True,
        journal=journal,
        action="rollout_resumed",
        detail="Production rollout orchestration resumed.",
    )


def advance_rollout_stage(
    *,
    execution_id: str,
    user_text: str,
    plan: dict[str, Any] | None = None,
    session_id: str = "",
) -> RolloutOrchestrationResult:
    journal, _ = get_or_create_rollout_journal(
        execution_id=execution_id,
        session_id=session_id,
        plan=plan,
    )
    current = str(journal.get("current_stage") or ROLLOUT_STAGES[0])
    statuses = dict(journal.get("stage_status") or {s: "pending" for s in ROLLOUT_STAGES})

    gate = assess_rollout_stage_gate(
        execution_id=execution_id,
        stage=current,  # type: ignore[arg-type]
        plan=plan,
        user_text=user_text,
        journal=journal,
        require_advance_phrase=True,
    )
    if not gate.ready_to_advance:
        return RolloutOrchestrationResult(
            success=False,
            journal=journal,
            action="advance_blocked",
            blockers=gate.blockers,
            detail="Production rollout advance blocked by governance gate.",
        )

    verification = load_verification_receipt(execution_id=execution_id) or {}
    checkpoints = assess_rollout_health_checkpoints(
        execution_id=execution_id,
        stage=current,  # type: ignore[arg-type]
        plan=plan,
    )
    journal["health_checkpoints"][current] = {
        cp.checkpoint_id: {"passed": cp.passed, "detail": cp.detail}
        for cp in checkpoints
    }

    statuses[current] = "completed"
    completed = list(journal.get("completed_stages") or [])
    if current not in completed:
        completed.append(current)

    next_stage = _next_stage(current)
    if next_stage:
        journal["current_stage"] = next_stage
        statuses[next_stage] = "in_progress"
        journal["blast_radius"] = BLAST_RADIUS_BY_STAGE.get(next_stage, "platform")  # type: ignore[arg-type]
        journal["orchestration_state"] = "active"
    else:
        journal["orchestration_state"] = "completed"

    journal["completed_stages"] = completed
    journal["stage_status"] = statuses
    journal = save_rollout_journal(journal)

    record_rollout_receipt(
        execution_id=execution_id,
        stage=current,
        action="stage_completed",
        status="rollout_stage_completed",
        detail=f"Governed completion of {current} stage (simulation only).",
        health_checkpoint="stage_gate_passed",
        evidence_snapshot={
            "verification": (verification.get("assessment") or {}),
            "checkpoints": [cp.checkpoint_id for cp in checkpoints if cp.passed],
        },
        blockers=[],
    )

    return RolloutOrchestrationResult(
        success=True,
        journal=journal,
        action="stage_advanced",
        stage_advanced_to=str(journal.get("current_stage") or ""),
        detail=(
            f"Completed rollout stage `{current}`."
            + (f" Now at `{next_stage}`." if next_stage else " All rollout stages complete.")
            + " No live production mutation performed."
        ),
    )


def assess_current_rollout_gate(
    *,
    execution_id: str,
    plan: dict[str, Any] | None = None,
) -> RolloutStageGateResult:
    journal = load_rollout_journal(execution_id=execution_id)
    if not journal:
        journal, _ = get_or_create_rollout_journal(execution_id=execution_id, plan=plan)
    current = str(journal.get("current_stage") or ROLLOUT_STAGES[0])
    return assess_rollout_stage_gate(
        execution_id=execution_id,
        stage=current,  # type: ignore[arg-type]
        plan=plan,
        journal=journal,
    )
