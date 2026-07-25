# SPDX-License-Identifier: Apache-2.0
"""Operational research hook for multi-agent / engineering runtimes."""

from __future__ import annotations

from typing import Any

from aethos_core.research.research_runtime import ResearchRunResult, run_research_query


def should_delegate_operational_research(user_request: str) -> bool:
    from aethos_core.research.planner import ResearchMode, plan_research

    raw = (user_request or "").strip()
    if not raw:
        return False
    mode = plan_research(raw).mode
    return mode in (ResearchMode.OPERATIONAL, ResearchMode.TECHNICAL, ResearchMode.DEEP_SYNTHESIS)


def attach_operational_research(
    user_request: str,
    *,
    session_id: str = "default",
    channel: str = "agent",
) -> ResearchRunResult | None:
    """Optional research substrate for operational / engineering prompts."""
    if not should_delegate_operational_research(user_request):
        return None
    return run_research_query(user_request, session_id=session_id, channel=channel)


def research_context_for_prompt(user_request: str, *, session_id: str = "default") -> dict[str, Any] | None:
    result = attach_operational_research(user_request, session_id=session_id)
    if result is None or not result.ok:
        return None
    return {
        "replay_id": result.replay_id,
        "artifact_ids": result.artifact_ids,
        "summary_excerpt": (result.reply or "")[:1200],
    }
