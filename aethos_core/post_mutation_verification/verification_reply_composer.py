# SPDX-License-Identifier: Apache-2.0
"""Compose post-mutation verification replies."""

from __future__ import annotations

from typing import Any, Literal

from aethos_core.post_mutation_verification.before_after_comparator import BeforeAfterComparison, compare_before_after
from aethos_core.post_mutation_verification.verification_context import VerificationContext, load_verification_context
from aethos_core.post_mutation_verification.verification_evidence_collector import (
    VerificationEvidence,
    collect_verification_evidence,
)
from aethos_core.post_mutation_verification.verification_status_classifier import (
    VerificationStatus,
    classify_verification_status,
    verification_status_label,
)

VerificationIntent = Literal[
    "verify_health",
    "did_recover",
    "did_hold",
    "what_changed",
    "fetch_logs",
]


def build_verification_bundle(
    *,
    session_id: str = "default",
    text: str | None = None,
    context: VerificationContext | None = None,
    lifecycle: Any | None = None,
) -> tuple[VerificationContext, VerificationEvidence, BeforeAfterComparison, VerificationStatus] | None:
    ctx = context or load_verification_context(session_id=session_id, text=text, lifecycle=lifecycle)
    if ctx is None:
        return None
    evidence = collect_verification_evidence(ctx)
    comparison = compare_before_after(evidence)
    status = classify_verification_status(evidence, comparison)
    from aethos_core.repair_memory.outcome_recorder import record_verification_outcome

    record_verification_outcome(
        ctx=ctx,
        evidence=evidence,
        comparison=comparison,
        status=status,
        session_id=session_id,
    )
    return ctx, evidence, comparison, status


def compose_verify_health_reply(
    *,
    session_id: str = "default",
    text: str | None = None,
    lifecycle: Any | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    bundle = build_verification_bundle(session_id=session_id, text=text, lifecycle=lifecycle)
    if bundle is None:
        return None
    ctx, evidence, comparison, status = bundle
    service_label = ctx.service or ctx.target_path
    lines = [
        "I'll verify the latest mutation I found:",
        "",
        f"**Target:** {ctx.target_path}",
        f"**Operation:** {ctx.operation.replace('_', ' ')}",
        "",
        "**Verification:**",
        f"- execution: {'completed' if evidence.execution_completed else 'unknown'}",
        f"- provider command: {'submitted' if evidence.provider_command_submitted else 'unknown'}",
        f"- health: {comparison.after_health}",
        f"- logs after restart: {_logs_availability(evidence)}",
        f"- status: **{verification_status_label(status)}**",
    ]
    if ctx.execution_job_id:
        lines.append(f"- execution job: `{ctx.execution_job_id}`")
    lines.extend(["", "**Conclusion:**", _conclusion_for_status(status, ctx, comparison)])
    meta = _meta(ctx, status, intent="verify_health")
    return "\n".join(lines), "post_mutation_verify_health", meta


def compose_did_recover_reply(
    *,
    session_id: str = "default",
    text: str | None = None,
    lifecycle: Any | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    bundle = build_verification_bundle(session_id=session_id, text=text, lifecycle=lifecycle)
    if bundle is None:
        return None
    ctx, evidence, comparison, status = bundle
    if status == "verified":
        reply = (
            f"Yes — recovery appears verified for **{ctx.target_path}**.\n\n"
            f"{comparison.change_summary}"
        )
    elif text and _did_restart_help_question(text):
        from aethos_core.repair_memory.recommendation_guard import compose_did_restart_help_reply
        from aethos_core.world_model.investigation_state import InvestigationState

        guard_state = InvestigationState(
            target=ctx.target_path,
            session_id=session_id,
            provider=ctx.provider,
            service=ctx.service or "",
            project=ctx.lifecycle.project or "",
            environment=ctx.lifecycle.environment or "",
        )
        guarded = compose_did_restart_help_reply(guard_state)
        if guarded:
            reply = guarded
        else:
            reply = _default_did_not_recover_reply(ctx, evidence, comparison)
    else:
        reply = _default_did_not_recover_reply(ctx, evidence, comparison)
    meta = _meta(ctx, status, intent="did_recover")
    return reply, "post_mutation_did_recover", meta


def _did_restart_help_question(text: str) -> bool:
    from aethos_core.repair_memory.recommendation_guard import is_did_restart_help_question

    return is_did_restart_help_question(text)


def _default_did_not_recover_reply(
    ctx: VerificationContext,
    evidence: VerificationEvidence,
    comparison: BeforeAfterComparison,
) -> str:
    reply = (
        "Not fully verified yet.\n\n"
        f"The **{ctx.operation.replace('_', ' ')}** was submitted and execution completed, "
        f"but **{ctx.service or ctx.target_path}** still appears "
        f"{comparison.after_health} / health is {comparison.after_health}."
    )
    if evidence.low_signal_logs:
        reply += " Logs only show low-signal WiredTiger activity."
    elif not evidence.logs_after_execution:
        reply += " Post-restart logs have not been collected yet."
    else:
        reply += f" {comparison.change_summary}"
    return reply


def compose_did_hold_reply(
    *,
    session_id: str = "default",
    text: str | None = None,
    lifecycle: Any | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    bundle = build_verification_bundle(session_id=session_id, text=text, lifecycle=lifecycle)
    if bundle is None:
        return None
    ctx, evidence, comparison, status = bundle
    if status == "verified" and not comparison.new_crash_after_restart:
        reply = (
            f"Yes — **{ctx.target_path}** recovery appears to be holding.\n\n"
            f"Latest health: **{comparison.after_health}**.\n"
            f"{comparison.change_summary}"
        )
    elif status == "still_stabilizing":
        reply = (
            f"Still stabilizing for **{ctx.target_path}**.\n\n"
            "The restart completed, but it is too early to confirm the recovery held."
        )
    else:
        reply = (
            f"Not confirmed yet for **{ctx.target_path}**.\n\n"
            f"Current verification: **{verification_status_label(status)}**.\n"
            f"{comparison.change_summary}"
        )
    meta = _meta(ctx, status, intent="did_hold")
    return reply, "post_mutation_did_hold", meta


def compose_what_changed_reply(
    *,
    session_id: str = "default",
    text: str | None = None,
    lifecycle: Any | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    bundle = build_verification_bundle(session_id=session_id, text=text, lifecycle=lifecycle)
    if bundle is None:
        return None
    ctx, evidence, comparison, status = bundle
    lines = [
        f"**What changed after the {ctx.operation.replace('_', ' ')} on {ctx.target_path}:**",
        "",
        "**Before restart:**",
        f"- status: {comparison.before_status}",
        f"- evidence: {comparison.before_evidence}",
        "",
        "**After restart:**",
        f"- status: {comparison.after_status}",
        f"- logs: {comparison.after_logs}",
        f"- health: {comparison.after_health}",
        "",
        "**Change summary:**",
        comparison.change_summary,
    ]
    meta = _meta(ctx, status, intent="what_changed")
    return "\n".join(lines), "post_mutation_what_changed", meta


def compose_fetch_logs_reply(
    *,
    session_id: str = "default",
    text: str | None = None,
    lifecycle: Any | None = None,
    log_limit: int | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    bundle = build_verification_bundle(session_id=session_id, text=text, lifecycle=lifecycle)
    if bundle is None:
        return None
    ctx, evidence, comparison, status = bundle
    limit = log_limit or 5
    if not evidence.log_summary:
        reply = (
            f"Fetching logs after the latest **{ctx.service or ctx.target_path}** restart.\n\n"
            f"No post-restart log bundle is stored yet for **{ctx.target_path}**.\n\n"
            "Execution completed, but verification logs are still missing or stale.\n\n"
            "Try **verify health** again after the readonly verification job finishes."
        )
    else:
        reply = (
            f"Fetching logs after the latest **{ctx.service or ctx.target_path}** restart.\n\n"
            f"**Latest {limit} post-restart logs:**\n\n"
            f"{evidence.log_summary}\n\n"
            f"Signal quality: {'low-signal' if evidence.low_signal_logs else 'usable'}.\n"
            f"Verification: **{verification_status_label(status)}**."
        )
    meta = _meta(ctx, status, intent="fetch_logs")
    return reply, "post_mutation_fetch_logs", meta


def compose_startup_log_check_reply(
    *,
    session_id: str = "default",
    text: str | None = None,
    lifecycle: Any | None = None,
    log_limit: int = 5,
) -> tuple[str, str, dict[str, str]] | None:
    bundle = build_verification_bundle(session_id=session_id, text=text, lifecycle=lifecycle)
    if bundle is None:
        return None
    ctx, evidence, comparison, status = bundle
    startup_found = evidence.startup_markers_present or "application startup" in evidence.log_summary.lower()
    marker_line = "found" if startup_found else "not found"
    if not evidence.log_summary:
        reply = (
            f"I checked the latest **{log_limit}** logs after the **{ctx.service or ctx.target_path}** restart.\n\n"
            "No post-restart log bundle is stored yet.\n\n"
            f"Startup marker: **{marker_line}**"
        )
    else:
        reply = (
            f"I checked the latest **{log_limit}** logs after the **{ctx.service or ctx.target_path}** restart.\n\n"
            f"Startup marker: **{marker_line}**\n\n"
            f"Latest logs:\n{evidence.log_summary}\n\n"
            f"Verification: **{verification_status_label(status)}**."
        )
    meta = _meta(ctx, status, intent="startup_log_check")
    return reply, "post_mutation_startup_log_check", meta


def _conclusion_for_status(
    status: VerificationStatus,
    ctx: VerificationContext,
    comparison: BeforeAfterComparison,
) -> str:
    if status == "verified":
        return f"Recovery appears verified for **{ctx.target_path}**. {comparison.change_summary}"
    if status == "still_stabilizing":
        return "Restart was submitted and execution completed, but the service is still stabilizing."
    if status == "failed_after_mutation":
        return (
            f"Restart completed, but **{ctx.service or ctx.target_path}** still appears failed. "
            f"{comparison.change_summary}"
        )
    if status == "regressed":
        return f"Service regressed after mutation. {comparison.change_summary}"
    if status == "blocked_by_missing_evidence":
        return "Execution evidence is incomplete — collect post-restart logs before trusting recovery."
    return (
        f"Restart evidence is inconclusive for **{ctx.target_path}**. "
        f"{comparison.change_summary}"
    )


def _logs_availability(evidence: VerificationEvidence) -> str:
    if evidence.startup_markers_present:
        return "available with startup markers"
    if evidence.logs_after_execution:
        return "available"
    if evidence.low_signal_logs:
        return "available but low-signal"
    return "unavailable"


def _logs_freshness(evidence: VerificationEvidence) -> str:
    if evidence.startup_markers_present:
        return "fresh after restart with startup markers"
    if evidence.logs_after_execution:
        return "present after restart"
    if evidence.low_signal_logs:
        return "low-signal after restart"
    return "not collected yet"


def _meta(ctx: VerificationContext, status: VerificationStatus, *, intent: str) -> dict[str, str]:
    meta = ctx.to_dict()
    meta.update(
        {
            "route_id": "post_mutation_verification",
            "post_mutation_verification_intent": intent,
            "post_mutation_verification_status": status,
            "matched_target": ctx.target_path,
            "last_checked_at": str(ctx.last_checked_at or ""),
        }
    )
    from aethos_core.repair_memory.historical_repair_lookup import lookup_latest_for_target

    latest = lookup_latest_for_target(ctx.target_path)
    if latest is not None:
        meta["repair_learning_recorded"] = "true"
        meta["repair_helped"] = "true" if latest.helped else "false"
        meta["repair_lesson"] = latest.lesson
    return meta


def compose_path_target_lifecycle_reply(
    *,
    lifecycle: Any,
    target_path: str,
) -> tuple[str, str, dict[str, str]]:
    op = str(getattr(lifecycle, "operation", "") or "restart").replace("_", " ")
    lines = [
        f"I found the latest **{op}** lifecycle for **{target_path}**.",
        "",
        f"- execution: {getattr(lifecycle, 'execution_status', 'unknown')}",
        f"- verification: {getattr(lifecycle, 'verification_status', 'unknown')}",
        "",
        "What would you like to do?",
        "- verify health",
        "- fetch post-restart logs",
        "- compare before/after",
    ]
    meta = {
        "route_id": "post_mutation_verification",
        "post_mutation_verification_intent": "target_lifecycle_menu",
        "matched_target": target_path,
        "global_lifecycle_index": "true",
    }
    if getattr(lifecycle, "execution_job_id", None):
        meta["execution_job_id"] = str(lifecycle.execution_job_id)
    return "\n".join(lines), "post_mutation_target_lifecycle_menu", meta
