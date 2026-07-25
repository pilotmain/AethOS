# SPDX-License-Identifier: Apache-2.0
"""Record repair outcomes from post-mutation verification."""

from __future__ import annotations

from typing import Any

from aethos_core.post_mutation_verification.before_after_comparator import BeforeAfterComparison
from aethos_core.post_mutation_verification.verification_context import VerificationContext
from aethos_core.post_mutation_verification.verification_evidence_collector import VerificationEvidence
from aethos_core.post_mutation_verification.verification_status_classifier import VerificationStatus
from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome, save_repair_attempt


def _helped_from_status(status: VerificationStatus) -> bool:
    return status == "verified"


def _build_evidence_notes(
    evidence: VerificationEvidence,
    comparison: BeforeAfterComparison,
    status: VerificationStatus,
) -> list[str]:
    notes: list[str] = []
    if evidence.provider_command_submitted:
        notes.append("provider command submitted")
    if _failed(comparison.after_health) or _failed(comparison.after_status):
        notes.append("health remains failed")
    if evidence.low_signal_logs:
        notes.append("logs after restart low-signal")
    elif evidence.logs_after_execution:
        notes.append("logs after restart available")
    elif not evidence.logs_after_execution:
        notes.append("post-restart logs unavailable")
    if status == "regressed":
        notes.append("service regressed after mutation")
    if status == "verified":
        notes.append("verification indicates recovery")
    return notes


def _lesson(ctx: VerificationContext, status: VerificationStatus, helped: bool) -> str:
    service = ctx.service or ctx.target_path
    op = ctx.operation.replace("_", " ")
    if helped:
        return f"The {op} appears to have helped **{service}**."
    if status in {"regressed", "failed_after_mutation"}:
        return f"{op.title()} did not resolve the **{service}** failure."
    if status == "still_stabilizing":
        return f"The {op} on **{service}** is still stabilizing — outcome not confirmed yet."
    return f"The {op} on **{service}** has not been confirmed as helpful yet."


def build_repair_outcome(
    *,
    ctx: VerificationContext,
    evidence: VerificationEvidence,
    comparison: BeforeAfterComparison,
    status: VerificationStatus,
    session_id: str = "default",
) -> RepairAttemptOutcome:
    helped = _helped_from_status(status)
    service = ctx.service or ""
    return RepairAttemptOutcome(
        target=ctx.target_path,
        operation=ctx.operation,
        attempted_at=__import__("datetime").datetime.now(tz=__import__("datetime").UTC).isoformat(),
        result=status,
        health_after=comparison.after_health or evidence.service_health,
        helped=helped,
        evidence=_build_evidence_notes(evidence, comparison, status),
        lesson=_lesson(ctx, status, helped),
        provider=ctx.provider,
        project=ctx.lifecycle.project or "",
        environment=ctx.lifecycle.environment or "",
        service=service,
        execution_job_id=ctx.execution_job_id or "",
        session_id=session_id,
        verification_status=status,
    )


def record_verification_outcome(
    *,
    ctx: VerificationContext,
    evidence: VerificationEvidence,
    comparison: BeforeAfterComparison,
    status: VerificationStatus,
    session_id: str = "default",
) -> RepairAttemptOutcome:
    outcome = build_repair_outcome(
        ctx=ctx,
        evidence=evidence,
        comparison=comparison,
        status=status,
        session_id=session_id,
    )
    save_repair_attempt(outcome)

    if ctx.execution_job_id:
        try:
            from aethos_core.runtime.jobs import job_store

            job = job_store.get(ctx.execution_job_id)
            if job is not None:
                job.params["repair_learning"] = outcome.to_dict()
                job.params["post_mutation_verification_status"] = status
        except Exception:
            pass

    from aethos_core.repair_memory.world_model_repair_bridge import sync_repair_learning_to_world_model

    sync_repair_learning_to_world_model(session_id=session_id, ctx=ctx, outcome=outcome)
    return outcome


def _failed(value: str) -> bool:
    low = str(value or "").lower()
    return low in {"failed", "crashed", "error", "unhealthy"}
