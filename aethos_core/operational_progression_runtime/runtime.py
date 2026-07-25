# SPDX-License-Identifier: Apache-2.0
"""Operational progression runtime aggregate — Phase 11.7.7."""

from __future__ import annotations

from typing import Any

from aethos_core.execution_progress_tracking.progress_tracker import get_execution_progress
from aethos_core.operational_progression_runtime.progression_runtime import orchestrate_operational_progression


def assess_operational_progression_runtime(
    *,
    session_id: str = "default",
    channel: str = "chat",
    user_text: str = "",
) -> dict[str, Any]:
    """Phase 11.7.7 — operational progression realism."""
    execution = (
        orchestrate_operational_progression(user_text=user_text, session_id=session_id, channel=channel)
        if user_text
        else None
    )
    progress = get_execution_progress(session_id=session_id)
    progression_qualified = bool(progress.get("progression_active")) or bool(
        execution and execution.get("progression_qualified")
    )
    return {
        "ok": True,
        "phase": "11.7.7",
        "converged": progression_qualified,
        "execution": execution,
        "execution_progress": progress,
        "summary": (
            "Operational progression active — agents evolve findings across conversational turns."
            if progression_qualified
            else "Operational progression ready — awaiting agent initialization or conclusion prompts."
        ),
    }
