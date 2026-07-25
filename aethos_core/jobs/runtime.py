# SPDX-License-Identifier: Apache-2.0
"""Durable agent jobs runtime aggregate — Phase 11.7.9."""

from __future__ import annotations

from typing import Any

from aethos_core.jobs.job_memory import build_job_continuity
from aethos_core.jobs.job_runtime import get_durable_jobs_state


def assess_durable_agent_jobs_runtime(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    state = get_durable_jobs_state(session_id=session_id)
    continuity = build_job_continuity(session_id=session_id)
    qualified = continuity.get("continuity_available", False) or bool(state.get("active_jobs"))
    return {
        **state,
        "converged": qualified,
        "channel": channel,
        "summary": (
            "Durable agent jobs active — background progression and artifact bridge enabled."
            if qualified
            else "Durable agent jobs ready — awaiting workspace job registration."
        ),
    }
