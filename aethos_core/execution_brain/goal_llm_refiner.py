# SPDX-License-Identifier: Apache-2.0
"""Optional LLM goal/reply refinement — never executes provider tools."""

from __future__ import annotations

from aethos_core.config import get_settings
from aethos_core.execution_brain.goal_planner import OperationalGoalPlan


def maybe_refine_operational_goal(
    plan: OperationalGoalPlan,
    *,
    user_text: str,
    session_id: str = "default",
) -> OperationalGoalPlan:
    settings = get_settings()
    if not settings.execution_brain_use_llm or not settings.use_real_llm:
        return plan
    from aethos_core.provider.completion import provider_configured

    if not provider_configured():
        return plan

    prompt = (
        "You refine operational goal labels for AethOS. Given the user message and planned goal, "
        "return ONE short headline (max 12 words) that clarifies intent. "
        "Do not add actions, credentials, mutations, or approvals.\n\n"
        f"User: {user_text}\n"
        f"Goal kind: {plan.kind}\n"
        f"Current headline: {plan.headline}\n"
        f"Provider: {plan.provider}\n"
    )
    try:
        from aethos_core.provider.completion import complete_chat

        result = complete_chat(prompt, session_id=session_id, channel="operational_kernel")
        headline = (result.text or "").strip().split("\n")[0][:120]
        if headline and result.used_llm:
            return OperationalGoalPlan(
                kind=plan.kind,
                headline=headline,
                provider=plan.provider,
                target_hint=plan.target_hint,
                user_text=plan.user_text,
                sub_goals=list(plan.sub_goals),
                readonly_goal=plan.readonly_goal,
                requires_context=list(plan.requires_context),
                is_continue=plan.is_continue,
            )
    except Exception:
        pass
    return plan


def maybe_refine_operational_reply(
    reply: str,
    *,
    goal_kind: str,
    provider: str,
    session_id: str = "default",
) -> tuple[str, bool]:
    settings = get_settings()
    if not settings.execution_brain_use_llm or not settings.use_real_llm:
        return reply, False
    from aethos_core.provider.completion import provider_configured

    if not provider_configured():
        return reply, False

    prompt = (
        "Rewrite this governed operational reply to be clearer and conversational. "
        "Preserve all facts, tool names, limits, recovery steps, and the line "
        "'No mutation has been performed.' when present. "
        "Do not add mutations, bypass approvals, or invent data.\n\n"
        f"Goal kind: {goal_kind}\nProvider: {provider}\n\n{reply}"
    )
    try:
        from aethos_core.provider.completion import complete_chat

        result = complete_chat(prompt, session_id=session_id, channel="operational_kernel")
        if result.used_llm and (result.text or "").strip():
            return result.text.strip(), True
    except Exception:
        pass
    return reply, False
