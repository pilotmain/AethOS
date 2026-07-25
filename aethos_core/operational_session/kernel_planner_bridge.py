# SPDX-License-Identifier: Apache-2.0
"""Bridge operational session kernel with execution brain planning."""

from __future__ import annotations

from dataclasses import dataclass

from aethos_core.execution_brain.conversation_plan_registry import (
    load_conversation_plan,
    upsert_plan_from_graph,
)
from aethos_core.execution_brain.goal_planner import OperationalGoalPlan, plan_operational_goal
from aethos_core.execution_brain.provider_tool_contract import get_tool_contract, recovery_hints_for_tool
from aethos_core.execution_brain.tool_planning_graph import ToolPlanningGraph, build_tool_planning_graph
from aethos_core.operational_session.active_subject_resolver import resolve_active_subject
from aethos_core.operational_session.operational_readonly_goal import ReadonlyGoal
from aethos_core.operational_session.operational_session import load_operational_session, record_operational_turn
from aethos_core.operational_session.railway_readonly_executor import ReadonlyExecutionResult, execute_railway_readonly
from aethos_core.operational_session.session_subject import SessionSubject
from aethos_core.operational_session.vercel_readonly_executor import execute_vercel_readonly


@dataclass
class PlannedLoopResult:
    ok: bool
    reply: str
    intent: str
    meta: dict[str, str]
    subject: SessionSubject
    goal_kind: str = ""


def run_planned_operational_loop(
    text: str,
    *,
    session_id: str = "default",
) -> PlannedLoopResult | None:
    session = load_operational_session(session_id=session_id)
    resolved = resolve_active_subject(text, session_id=session_id)
    goal = plan_operational_goal(text, subject=resolved.subject, session=session)
    if goal is None:
        return None

    from aethos_core.execution_brain.goal_llm_refiner import maybe_refine_operational_goal, maybe_refine_operational_reply

    goal = maybe_refine_operational_goal(goal, user_text=text, session_id=session_id)

    if goal.is_continue:
        return _continue_active_plan(session_id=session_id, subject=resolved.subject)

    graph = build_tool_planning_graph(goal)

    if goal.kind == "deploy_planning":
        reply = compose_deploy_plan_reply(goal, graph)
        reply, used_llm = maybe_refine_operational_reply(
            reply, goal_kind=goal.kind, provider=goal.provider, session_id=session_id
        )
        upsert_plan_from_graph(
            session_id=session_id,
            goal=goal,
            graph=graph,
            suggested_next_action=_suggested_next_from_graph(graph),
        )
        from aethos_core.operational_session.goal_completion_registry import record_goal_started

        record_goal_started(
            session_id=session_id,
            headline=goal.headline,
            provider=goal.provider or "railway",
            goal_kind=goal.kind,
            user_text=text,
            steps_pending=[step.step_id for step in graph.steps],
        )
        record_operational_turn(
            session_id=session_id,
            user_text=text,
            subject=SessionSubject(provider=goal.provider, subject_source="plan"),
            operation="deploy_planning",
            reply_intent="operational_kernel_deploy_plan",
            result_summary=goal.headline,
        )
        return PlannedLoopResult(
            ok=True,
            reply=reply,
            intent="operational_kernel_deploy_plan",
            meta={**_meta(session_id, goal, graph, planning_only=True), **({"brain_used_llm": "true"} if used_llm else {})},
            subject=resolved.subject,
            goal_kind=goal.kind,
        )

    if goal.kind == "readonly_execute" and goal.readonly_goal is not None:
        recovery_applied = False
        result = _execute_readonly_goal(goal.readonly_goal, resolved.subject, session_id=session_id)
        if not result.ok and result.tool_id:
            error_code = _error_code_from_result(result)
            skip_recovery = _should_skip_readonly_recovery(result, error_code=error_code)
            if not skip_recovery:
                recovery = compose_tool_recovery_reply(
                    tool_id=result.tool_id,
                    error_code=error_code,
                    provider=goal.provider or resolved.subject.provider or "railway",
                    operation=result.operation,
                )
                if recovery:
                    result = ReadonlyExecutionResult(
                        ok=False,
                        reply=recovery,
                        operation=result.operation,
                        tool_id=result.tool_id,
                    )
                    recovery_applied = True
                else:
                    recovery_applied = False
            elif _should_preserve_executor_reply(result):
                recovery_applied = True
            else:
                recovery_applied = False
        else:
            recovery_applied = False
        subject = result.subject or resolved.subject
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
        upsert_plan_from_graph(
            session_id=session_id,
            goal=goal,
            graph=_mark_readonly_completed(graph, result.tool_id),
            suggested_next_action="",
        )
        reply = result.reply
        used_llm = False
        if not recovery_applied and not _should_preserve_executor_reply(result):
            reply, used_llm = maybe_refine_operational_reply(
                reply,
                goal_kind=goal.kind,
                provider=goal.provider or resolved.subject.provider or "railway",
                session_id=session_id,
            )
        meta = _meta(session_id, goal, graph)
        if result.operation:
            meta["operation"] = result.operation
        if recovery_applied:
            meta["recovery_applied"] = "true"
        if used_llm:
            meta["brain_used_llm"] = "true"
        if result.ok:
            from aethos_core.operational_session.goal_completion_registry import record_readonly_goal_completed

            record_readonly_goal_completed(
                session_id=session_id,
                operation=result.operation,
                provider=goal.provider or resolved.subject.provider or "railway",
                user_text=text,
            )
        else:
            from aethos_core.operational_session.goal_completion_registry import record_goal_blocked

            record_goal_blocked(session_id=session_id, reason=result.summary)
        return PlannedLoopResult(
            ok=result.ok,
            reply=reply,
            intent=f"operational_kernel_{result.operation}",
            meta=meta,
            subject=subject,
            goal_kind=goal.kind,
        )

    return None


def compose_deploy_plan_reply(goal: OperationalGoalPlan, graph: ToolPlanningGraph) -> str:
    lines = [
        f"**Goal:** {goal.headline}",
        "",
        "Here is the governed plan I would follow — **planning only**, no mutations yet:",
        "",
    ]
    for idx, step in enumerate(graph.steps, start=1):
        tier = "readonly" if step.readonly else step.tool_type
        lines.append(f"{idx}. **{step.label}** → `{step.tool_id}` ({tier})")
    lines.extend(
        [
            "",
            "**Recommended next action:**",
            f"1. {_suggested_next_from_graph(graph)}",
            "",
            "Reply **continue** when you want me to execute the next readonly planning step, "
            "or approve governed preflight when we reach deployment.",
            "",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def compose_tool_recovery_reply(
    *,
    tool_id: str,
    error_code: str,
    provider: str,
    operation: str = "",
) -> str:
    from aethos_core.execution_brain.execution_recovery_engine import (
        RecoveryPath,
        compose_recovery_narrative,
        recovery_path_for_blocker,
    )
    from aethos_core.provider_e2e_readiness.blocker_mapping import ReadinessBlocker

    hints = recovery_hints_for_tool(tool_id)
    code = error_code or (hints[0] if hints else "UNKNOWN_BLOCKER")
    blocker = ReadinessBlocker(
        code=code,
        meaning=f"Tool `{tool_id}` did not complete successfully.",
        required_action="Choose a recovery path below.",
        safe_next_command="show Railway projects" if provider == "railway" else "validate Vercel connection",
    )
    recovery = recovery_path_for_blocker(blocker)
    if code == "RAILWAY_TARGET_SERVICE_MISSING" and _is_readonly_inventory_operation(operation):
        recovery = recovery_path_for_blocker(
            ReadinessBlocker(
                code=code,
                meaning="No existing service matched the requested target.",
                required_action="Specify the Railway project, environment, and service name explicitly.",
                safe_next_command="show Railway projects",
            )
        )
        readonly_recovery = RecoveryPath(
            blocker_code=recovery.blocker_code,
            headline=recovery.headline,
            cause=recovery.cause,
            next_action=recovery.next_action,
            recovery_steps=recovery.recovery_steps,
            safe_next_command=recovery.safe_next_command,
            can_continue_after_fix=False,
            post_recovery_steps=(),
        )
        return compose_recovery_narrative(recovery=readonly_recovery, provider=provider)
    if code == "RAILWAY_TARGET_SERVICE_MISSING":
        recovery = recovery_path_for_blocker(
            ReadinessBlocker(
                code=code,
                meaning="No existing service matched the requested target.",
                required_action="Pick a recovery path:",
                safe_next_command="show Railway projects",
            )
        )
        lines = [
            compose_recovery_narrative(recovery=recovery, provider=provider),
            "",
            "**Possible recovery:**",
            "1. create new service (greenfield deploy path)",
            "2. select existing service from inventory",
            "3. inspect Railway projects",
            "",
            "**Recommended:** create new service via governed greenfield deploy.",
        ]
        return "\n".join(lines)
    return compose_recovery_narrative(recovery=recovery, provider=provider)


def _is_readonly_inventory_operation(operation: str) -> bool:
    return operation in {"fetch_logs", "health_check", "list_inventory", "deployment_status", "validate_connection"}


def _should_skip_readonly_recovery(result: ReadonlyExecutionResult, *, error_code: str) -> bool:
    if result.operation == "fetch_logs" and "**Vercel logs" in (result.reply or ""):
        return True
    if error_code in {"RAILWAY_TARGET_SERVICE_MISSING", "VERCEL_TARGET_PROJECT_MISSING"} and _is_readonly_inventory_operation(
        result.operation
    ):
        return _executor_reply_has_readonly_recovery(result.reply)
    return False


def _executor_reply_has_readonly_recovery(reply: str | None) -> bool:
    lower = (reply or "").lower()
    return "show railway projects" in lower or "show vercel projects" in lower


def _should_preserve_executor_reply(result: ReadonlyExecutionResult) -> bool:
    if result.ok:
        return False
    if _is_readonly_inventory_operation(result.operation) and _executor_reply_has_readonly_recovery(result.reply):
        return True
    return False


def _continue_active_plan(*, session_id: str, subject: SessionSubject) -> PlannedLoopResult | None:
    plan = load_conversation_plan(session_id=session_id)
    if plan is None or plan.graph is None:
        return PlannedLoopResult(
            ok=False,
            reply="There is no active operational plan to continue. Start with a goal like `show Railway projects` or `deploy AethOS to Railway`.",
            intent="operational_kernel_no_plan",
            meta={"route_id": "operational_conversation_kernel", "kernel_v2": "true"},
            subject=subject,
        )

    graph = plan.graph
    step = graph.next_readonly_step()
    if step is None:
        reply = (
            f"Plan **{plan.active_goal}** has no pending readonly steps.\n\n"
            f"Suggested next action: **{plan.suggested_next_action or 'await governed approval'}**\n\n"
            "No mutation has been performed."
        )
        return PlannedLoopResult(
            ok=True,
            reply=reply,
            intent="operational_kernel_plan_status",
            meta={"route_id": "operational_conversation_kernel", "kernel_v2": "true"},
            subject=subject,
        )

    if step.tool_id.startswith("local_workspace.") or step.tool_id.startswith("git."):
        reply = _compose_workspace_step_reply(step)
        from aethos_core.execution_brain.tool_planning_graph import mark_step_completed

        updated = mark_step_completed(graph, step.step_id, summary="planned")
        upsert_plan_from_graph(
            session_id=session_id,
            goal=OperationalGoalPlan(kind="continue_plan", headline=plan.active_goal, provider=plan.provider),
            graph=updated,
            suggested_next_action=_suggested_next_from_graph(updated),
        )
        return PlannedLoopResult(
            ok=True,
            reply=reply,
            intent="operational_kernel_plan_step",
            meta={"route_id": "operational_conversation_kernel", "tool_id": step.tool_id, "kernel_v2": "true"},
            subject=subject,
        )

    readonly_goal = _goal_from_tool_step(step, subject)
    if readonly_goal is None:
        return None
    provider = plan.provider or subject.provider or "railway"
    result = _execute_readonly_goal(readonly_goal, subject, session_id=session_id)
    from aethos_core.execution_brain.tool_planning_graph import mark_step_completed, mark_step_failed

    if result.ok:
        updated = mark_step_completed(graph, step.step_id, summary=result.summary)
    else:
        updated = mark_step_failed(graph, step.step_id, error_code=_error_code_from_result(result), summary=result.summary)
    from aethos_core.operational_session.goal_completion_registry import (
        record_goal_completed,
        record_goal_progress,
    )

    record_goal_progress(session_id=session_id, step_id=step.step_id, steps_pending=[s.step_id for s in updated.steps if s.status == "pending"])
    if updated.next_readonly_step() is None and result.ok:
        record_goal_completed(session_id=session_id)
    upsert_plan_from_graph(
        session_id=session_id,
        goal=OperationalGoalPlan(kind="continue_plan", headline=plan.active_goal, provider=provider),
        graph=updated,
        suggested_next_action=_suggested_next_from_graph(updated),
    )
    return PlannedLoopResult(
        ok=result.ok,
        reply=result.reply,
        intent="operational_kernel_plan_step",
        meta={"route_id": "operational_conversation_kernel", "tool_id": step.tool_id, "kernel_v2": "true"},
        subject=result.subject or subject,
    )


def _compose_workspace_step_reply(step) -> str:
    if step.tool_id == "local_workspace.discover":
        try:
            from aethos_core.local_workspace.portfolio import discover_projects

            payload = discover_projects(rescan=False, auto_register=False)
            projects = list(payload.get("projects") or [])
            names = ", ".join(str(row.get("name") or "?") for row in projects[:5]) or "none found"
            body = f"Workspace discovery found: **{names}**."
        except Exception:
            body = "Workspace discovery is configured but returned no portfolio entries."
    else:
        body = "Git remote resolution would run against the active workspace (readonly planning step)."
    return (
        f"**Plan step:** {step.label}\n\n"
        f"{body}\n\n"
        "Reply **continue** for the next readonly planning step.\n\n"
        "No mutation has been performed."
    )


def _execute_readonly_goal(
    goal: ReadonlyGoal,
    subject: SessionSubject,
    *,
    session_id: str,
) -> ReadonlyExecutionResult:
    from aethos_core.operational_target_resolution.provider_intent_guard import is_valid_vercel_project_hint

    # §5 — a garbage/quantifier "project" (e.g. "both") must never route to Vercel.
    provider = subject.provider or (
        "vercel" if (subject.vercel_project and is_valid_vercel_project_hint(subject.vercel_project)) else "railway"
    )
    if provider == "vercel":
        vercel = execute_vercel_readonly(goal, subject, session_id=session_id)
        return ReadonlyExecutionResult(
            ok=vercel.ok,
            reply=vercel.reply,
            operation=vercel.operation,
            tool_id=vercel.tool_id,
            summary=vercel.summary,
            subject=vercel.subject,
            log_limit=vercel.log_limit,
        )
    return execute_railway_readonly(goal, subject, session_id=session_id)


def _goal_from_tool_step(step, subject: SessionSubject) -> ReadonlyGoal | None:
    mapping = {
        "railway.discover_projects": "list_inventory",
        "railway.fetch_logs": "fetch_logs",
        "railway.verify_deployment": "health_check",
        "vercel.discover_projects": "list_inventory",
        "vercel.fetch_logs": "fetch_logs",
        "vercel.verify_deployment": "deployment_status",
        "vercel.validate_token": "validate_connection",
        "railway.validate_token": "validate_connection",
    }
    operation = mapping.get(step.tool_id)
    if operation is None:
        return None
    return ReadonlyGoal(operation=operation, log_limit=5, user_text=step.label)


def _suggested_next_from_graph(graph: ToolPlanningGraph) -> str:
    step = graph.next_pending_step()
    if step is None:
        return "Complete governed preflight approval in Mission Control"
    contract = get_tool_contract(step.tool_id)
    return contract.description if contract else step.label


def _mark_readonly_completed(graph: ToolPlanningGraph, tool_id: str) -> ToolPlanningGraph:
    from aethos_core.execution_brain.tool_planning_graph import mark_step_completed

    for step in graph.steps:
        if step.tool_id == tool_id and step.status == "pending":
            return mark_step_completed(graph, step.step_id, summary="executed")
    return graph


def _error_code_from_result(result: ReadonlyExecutionResult) -> str:
    lower = (result.reply or "").lower()
    if "no vercel project named" in lower:
        return "VERCEL_TARGET_PROJECT_MISSING"
    if "no railway service named" in lower:
        return "RAILWAY_TARGET_SERVICE_MISSING"
    if "inventory" in lower and "fail" in lower:
        return "RAILWAY_INVENTORY_UNAVAILABLE"
    if "could not resolve" in lower or "couldn't resolve" in lower:
        return "RAILWAY_TARGET_SERVICE_MISSING"
    if "token" in lower and "vercel" in lower:
        return "VERCEL_TOKEN_MISSING"
    return "UNKNOWN_BLOCKER"


def _meta(
    session_id: str,
    goal: OperationalGoalPlan,
    graph: ToolPlanningGraph,
    *,
    planning_only: bool = False,
) -> dict[str, str]:
    meta = {
        "route_id": "operational_conversation_kernel",
        "matched_module": "execution_brain.kernel_planner_bridge",
        "session_id": session_id,
        "kernel_v2": "true",
        "goal_kind": goal.kind,
        "plan_steps": str(len(graph.steps)),
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
    }
    if planning_only:
        meta["planning_only"] = "true"
    if goal.provider:
        meta["readonly_provider"] = goal.provider
    return meta
