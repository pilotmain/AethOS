# SPDX-License-Identifier: Apache-2.0
"""Intervention timing — decides when to interrupt."""

from __future__ import annotations

from typing import Any


def assess_intervention_timing(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.presence.calm.calm_presence_runtime import get_calm_presence_state
    from aethos_core.presence.interruption_policy import interruption_stats
    from aethos_core.presence.live.live_presence_runtime import get_live_focus

    calm = get_calm_presence_state(session_id=session_id)
    focus = get_live_focus(session_id=session_id)
    stats = interruption_stats()
    minutes = float(focus.get("duration_minutes") or 0)

    should_interrupt = calm.get("should_interrupt", True)
    reason = "Normal pacing — operator available for calm guidance."
    if minutes >= 90 and calm.get("quiet_mode_recommended"):
        should_interrupt = False
        reason = "Focus protection — you've been deep in work ~90m with no production outage. I'll summarize later."
    elif int(stats.get("suppressed") or 0) > 3:
        reason = "Interruption budget preserved — recent low-value alerts suppressed."

    return {
        "ok": True,
        "should_interrupt": should_interrupt,
        "reason": reason,
        "interruption_budget_remaining": calm.get("interruption_budget_remaining", 3),
        "quiet_mode": calm.get("quiet_mode_recommended", False),
        "autonomous_execution_blocked": True,
    }
