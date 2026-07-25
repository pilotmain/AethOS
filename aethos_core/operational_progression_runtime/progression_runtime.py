# SPDX-License-Identifier: Apache-2.0
"""Operational progression runtime orchestration — Phase 11.7.7."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.entity_compat import infer_progression_intent
from aethos_core.conversation.progression_compat import compose_agent_conclusion_reply
from aethos_core.execution_progress_tracking.progress_tracker import get_execution_progress, initialize_execution_progress
from aethos_core.live_operational_grounding.regression_guardrails import assess_regression_guardrails
from aethos_core.workspace_evolution.workspace_evolution import evolve_workspace


def orchestrate_operational_progression(
    *,
    user_text: str,
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any] | None:
    intent_info = infer_progression_intent(user_text)
    if not intent_info.get("progression_prompt"):
        return None

    target = intent_info.get("target_agent")
    reply = compose_agent_conclusion_reply(session_id=session_id, agent_name=target)
    workspace_evolution = evolve_workspace(session_id=session_id)
    progress = get_execution_progress(session_id=session_id)
    guardrails = assess_regression_guardrails(reply=reply, grounded=True)

    return {
        "reply": reply,
        "intent": "agent_conclusion",
        "lane": "operational_progression",
        "grounded": True,
        "target_agent": target,
        "progression": progress,
        "workspace_evolution": workspace_evolution,
        "regression_guardrails": guardrails,
        "progression_qualified": guardrails.get("guardrails_qualified", True) and progress.get("progression_active"),
        "summary": "Operational progression realism active — evolving agent findings.",
    }


def seed_operational_progression(*, session_id: str, agent_names: list[str]) -> dict[str, Any]:
    progress = initialize_execution_progress(session_id=session_id, agent_names=agent_names)
    evolve_workspace(session_id=session_id)
    return progress
