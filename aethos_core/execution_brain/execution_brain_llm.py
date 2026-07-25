# SPDX-License-Identifier: Apache-2.0
"""Optional LLM reasoning layer for execution brain responses."""

from __future__ import annotations

from aethos_core.config import get_settings
from aethos_core.execution_brain.execution_result import ExecutionPlanResult


def maybe_enhance_execution_reply(
    *,
    base_reply: str,
    plan: ExecutionPlanResult,
    session_id: str = "default",
) -> tuple[str, bool]:
    """Polish explanation with LLM when enabled — never for provider API calls or governance."""
    settings = get_settings()
    if not settings.execution_brain_use_llm or not settings.use_real_llm:
        return base_reply, False

    from aethos_core.provider.completion import provider_configured

    if not provider_configured():
        return base_reply, False

    prompt = (
        "You are the AethOS execution brain reasoning layer. Rewrite the following governed operational "
        "response to be clearer and more agentic while preserving every factual claim, blocker code, "
        "approval requirement, and safe next command. Do not add new actions, bypass approvals, or "
        "invent credentials. Keep markdown structure.\n\n"
        f"Provider: {plan.provider}\n"
        f"Goal: {plan.goal_summary}\n"
        f"Steps completed: {plan.completed_count}\n\n"
        f"Base response:\n{base_reply}"
    )
    try:
        from aethos_core.provider.completion import complete_chat

        result = complete_chat(prompt, session_id=session_id, channel="execution_brain")
        if result.used_llm and (result.text or "").strip():
            return result.text.strip(), True
    except Exception:
        pass
    return base_reply, False
