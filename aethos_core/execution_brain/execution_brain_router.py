# SPDX-License-Identifier: Apache-2.0
"""Chat router for the agentic execution brain."""

from __future__ import annotations

from aethos_core.config import get_settings
from aethos_core.execution_brain.execution_brain import (
    compose_execution_brain_reply,
    record_plan_metrics,
    run_execution_brain,
)
from aethos_core.execution_brain.execution_brain_llm import maybe_enhance_execution_reply
from aethos_core.execution_brain.execution_goal import is_execution_brain_goal


def route_execution_brain_turn(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    settings = get_settings()
    if not settings.execution_brain_enabled:
        return None
    if not is_execution_brain_goal(text):
        return None

    plan = run_execution_brain(text, session_id=session_id)
    if plan is None:
        return None

    base_reply = plan.recovery_summary or compose_execution_brain_reply(plan)
    reply, used_llm = maybe_enhance_execution_reply(base_reply=base_reply, plan=plan, session_id=session_id)
    record_plan_metrics(plan, session_id=session_id)

    intent = "execution_brain_railway_pilot" if plan.provider == "railway" else "execution_brain_turn"
    if plan.awaiting_approval:
        intent = "execution_brain_preflight_created"
    elif plan.blocked:
        intent = "execution_brain_recovery"

    meta = _meta(plan=plan, session_id=session_id, used_llm=used_llm)
    return reply, intent, meta


def _meta(*, plan, session_id: str, used_llm: bool) -> dict[str, str]:
    return {
        "route_id": "execution_brain",
        "matched_module": "execution_brain.execution_brain_router",
        "provider": plan.provider,
        "execution_brain_stage": "recovery" if plan.blocked else ("preflight" if plan.awaiting_approval else "progress"),
        "readonly": "true" if not plan.awaiting_approval else "false",
        "mutation_performed": "false",
        "execution_started": "false",
        "preflight_created": "true" if plan.awaiting_approval else "false",
        "presentation_bypass": "true",
        "suppress_governance_footer": "true",
        "tier": "tier_0_cognition",
        "brain_used_llm": "true" if used_llm else "false",
        "brain_steps_completed": str(plan.completed_count),
        "brain_blocker_count": str(len(plan.blockers)),
        "job_id": plan.job_id or "",
        "session_id": session_id,
    }
