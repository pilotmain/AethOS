# SPDX-License-Identifier: Apache-2.0
"""Execution brain — perceive, plan, execute readonly steps, recover, hand off to governance."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.execution_brain.execution_context import ExecutionContext
from aethos_core.execution_brain.execution_goal import ExecutionGoal, detect_execution_goal
from aethos_core.execution_brain.execution_memory import load_execution_memory, update_execution_memory
from aethos_core.execution_brain.execution_recovery_engine import compose_recovery_narrative, recovery_path_for_blocker
from aethos_core.execution_brain.execution_result import ExecutionPlanResult, ExecutionStepResult
from aethos_core.execution_brain.provider_tool_registry import tools_for_goal


def run_execution_brain(
    text: str,
    *,
    session_id: str = "default",
) -> ExecutionPlanResult | None:
    settings = get_settings()
    if not settings.execution_brain_enabled:
        return None

    goal = detect_execution_goal(text)
    if goal is None:
        return None

    if goal.provider == "railway" and settings.execution_brain_railway_pilot_enabled:
        from aethos_core.execution_brain.railway_pilot import run_railway_execution_brain

        return run_railway_execution_brain(goal, session_id=session_id)

    if goal.provider == "vercel" and settings.execution_brain_vercel_enabled:
        return _run_vercel_placeholder(goal, session_id=session_id)

    return None


def _run_vercel_placeholder(goal: ExecutionGoal, *, session_id: str) -> ExecutionPlanResult:
    _ = session_id
    return ExecutionPlanResult(
        goal_summary=goal.user_text,
        provider="vercel",
        steps=[
            ExecutionStepResult(
                step_id="vercel.pilot_pending",
                label="Vercel agentic pilot",
                status="blocked",
                detail="Vercel agentic execution pilot is not enabled yet. Railway pilot must pass first.",
                blocker_code="VERCEL_PILOT_NOT_ENABLED",
            )
        ],
        blockers=["VERCEL_PILOT_NOT_ENABLED"],
        recovery_summary="Complete Railway agentic pilot before expanding to Vercel.",
    )


def compose_execution_brain_reply(plan: ExecutionPlanResult) -> str:
    if plan.recovery_summary:
        return plan.recovery_summary

    lines = [
        f"**Working on your {plan.provider.title()} goal**",
        "",
        plan.goal_summary,
        "",
        "**Progress:**",
    ]
    for step in plan.steps:
        icon = {
            "completed": "done",
            "blocked": "blocked",
            "failed": "failed",
            "awaiting_approval": "awaiting approval",
            "skipped": "skipped",
        }.get(step.status, step.status)
        lines.append(f"- {step.label}: **{icon}**")
        if step.detail and step.status != "completed":
            lines.append(f"  {step.detail}")

    if plan.awaiting_approval and plan.job_id:
        lines.extend(
            [
                "",
                f"Governed preflight job `{plan.job_id}` is ready for Mission Control approval.",
                "No mutation has been executed yet.",
            ]
        )
    elif plan.completion_ready:
        lines.extend(["", "Readonly preparation is complete. Governed execution can proceed after approval."])

    if plan.next_executable_step:
        lines.extend(["", f"**Next step:** {plan.next_executable_step}"])

    lines.append("")
    lines.append(f"No unauthorized {plan.provider.title()} mutation has been performed.")
    return "\n".join(lines)


def compose_blocked_plan_reply(
    *,
    plan: ExecutionPlanResult,
    blockers: list[Any],
    provider: str,
) -> str:
    from aethos_core.execution_brain.execution_recovery_engine import compose_blocked_execution_reply

    preview = tuple(
        step.label
        for step in plan.steps
        if step.status not in {"completed", "blocked", "failed"}
    )
    return compose_blocked_execution_reply(
        blockers=blockers,
        provider=provider,
        post_recovery_preview=preview or None,
    )


def build_execution_context(goal: ExecutionGoal, *, session_id: str) -> ExecutionContext:
    settings = get_settings()
    memory = load_execution_memory(session_id=session_id)
    return ExecutionContext(
        session_id=session_id,
        goal=goal,
        available_tools=tools_for_goal(
            provider=goal.provider,
            requires_env=goal.requires_env,
            requires_verify=goal.requires_verify,
        ),
        mutation_execution_enabled=settings.mutation_execution_enabled,
        provider_env_mutations_enabled=settings.provider_env_var_mutations_enabled,
        prior_failures=list(memory.prior_failures),
        active_job_id=memory.active_job_id,
    )


def record_plan_metrics(plan: ExecutionPlanResult, *, session_id: str) -> None:
    metric = "brain_turn_completed"
    if plan.blocked:
        metric = "brain_turn_blocked"
    elif plan.awaiting_approval:
        metric = "brain_turn_awaiting_approval"
    update_execution_memory(session_id=session_id, increment_metric=metric)
    if plan.blockers:
        update_execution_memory(session_id=session_id, failure_code=plan.blockers[0])
