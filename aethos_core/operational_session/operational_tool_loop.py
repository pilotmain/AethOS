# SPDX-License-Identifier: Apache-2.0
"""Operational tool loop — subject → goal → provider tool → human response."""

from __future__ import annotations

from dataclasses import dataclass

from aethos_core.operational_session.active_subject_resolver import resolve_active_subject
from aethos_core.operational_session.operational_readonly_goal import ReadonlyGoal, classify_readonly_goal
from aethos_core.operational_session.operational_session import load_operational_session, record_operational_turn
from aethos_core.operational_session.railway_readonly_executor import ReadonlyExecutionResult, execute_railway_readonly
from aethos_core.operational_session.session_subject import SessionSubject
from aethos_core.operational_session.vercel_readonly_executor import VercelReadonlyResult, execute_vercel_readonly


@dataclass
class ToolLoopResult:
    ok: bool
    reply: str
    intent: str
    meta: dict[str, str]
    subject: SessionSubject


def run_operational_tool_loop(
    text: str,
    *,
    session_id: str = "default",
) -> ToolLoopResult | None:
    from aethos_core.operational_session.kernel_planner_bridge import run_planned_operational_loop

    planned = run_planned_operational_loop(text, session_id=session_id)
    if planned is not None:
        return ToolLoopResult(
            ok=planned.ok,
            reply=planned.reply,
            intent=planned.intent,
            meta=planned.meta,
            subject=planned.subject,
        )

    session = load_operational_session(session_id=session_id)
    resolved = resolve_active_subject(text, session_id=session_id)
    if resolved.needs_clarification:
        goal = classify_readonly_goal(text, subject=resolved.subject, session=session)
        if goal is None:
            return None
        return ToolLoopResult(
            ok=False,
            reply=resolved.clarification_prompt + "\n\nNo mutation has been performed.",
            intent="operational_kernel_needs_target",
            meta=_meta(session_id=session_id, operation=goal.operation, provider=""),
            subject=resolved.subject,
        )

    goal = classify_readonly_goal(text, subject=resolved.subject, session=session)
    if goal is None:
        return None

    provider = (resolved.subject.provider or "").lower()
    if not provider:
        if resolved.subject.vercel_project:
            provider = "vercel"
        elif resolved.subject.project or resolved.subject.services:
            provider = "railway"

    if provider == "railway":
        result = execute_railway_readonly(goal, resolved.subject, session_id=session_id)
        return _finalize(text, goal, result, session_id=session_id, provider="railway")

    if provider == "vercel":
        vercel_result = execute_vercel_readonly(goal, resolved.subject, session_id=session_id)
        railway_like = ReadonlyExecutionResult(
            ok=vercel_result.ok,
            reply=vercel_result.reply,
            operation=vercel_result.operation,
            tool_id=vercel_result.tool_id,
            summary=vercel_result.summary,
            subject=vercel_result.subject,
            log_limit=vercel_result.log_limit,
        )
        loop = _finalize(text, goal, railway_like, session_id=session_id, provider="vercel")
        if loop is not None and vercel_result.deployment_id:
            loop.meta["deployment_id"] = vercel_result.deployment_id
        return loop

    return ToolLoopResult(
        ok=False,
        reply=f"Readonly operational tools for `{provider or 'unknown'}` are not enabled in the kernel yet.",
        intent="operational_kernel_unsupported_provider",
        meta=_meta(session_id=session_id, operation=goal.operation, provider=provider),
        subject=resolved.subject,
    )


def _finalize(
    text: str,
    goal: ReadonlyGoal,
    result: ReadonlyExecutionResult,
    *,
    session_id: str,
    provider: str,
) -> ToolLoopResult:
    subject = result.subject or SessionSubject(provider=provider, subject_source="session")
    record_operational_turn(
        session_id=session_id,
        user_text=text,
        subject=subject,
        operation=result.operation,
        reply_intent=f"operational_kernel_{result.operation}",
        result_summary=result.summary,
        log_limit=result.log_limit,
        tool_id=result.tool_id,
    )
    return ToolLoopResult(
        ok=result.ok,
        reply=result.reply,
        intent=f"operational_kernel_{result.operation}",
        meta=_meta(
            session_id=session_id,
            operation=result.operation,
            provider=provider,
            tool_id=result.tool_id,
            subject=subject,
        ),
        subject=subject,
    )


def _meta(
    *,
    session_id: str,
    operation: str,
    provider: str,
    tool_id: str = "",
    subject: SessionSubject | None = None,
) -> dict[str, str]:
    meta = {
        "route_id": "operational_conversation_kernel",
        "matched_module": "operational_session.operational_tool_loop",
        "session_id": session_id,
        "kernel_operation": operation,
        "readonly_provider": provider,
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
    }
    if tool_id:
        meta["tool_id"] = tool_id
    if subject is not None:
        if subject.path_label():
            meta["active_subject"] = subject.path_label()
        if subject.services:
            meta["active_services"] = ",".join(subject.services)
    return meta
