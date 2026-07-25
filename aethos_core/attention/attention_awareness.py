# SPDX-License-Identifier: Apache-2.0
"""Attention awareness — operator energy and interruption timing."""

from __future__ import annotations

from time import time
from typing import Any


def assess_operator_attention(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.presence.calm.calm_presence_runtime import get_calm_presence_state
    from aethos_core.presence.live.live_presence_runtime import get_live_focus

    calm = get_calm_presence_state(session_id=session_id)
    focus = get_live_focus(session_id=session_id)
    minutes = float(focus.get("duration_minutes") or calm.get("focus_minutes") or 0)

    fatigue_level = "low"
    if minutes >= 180:
        fatigue_level = "high"
    elif minutes >= 90:
        fatigue_level = "moderate"

    recommendation_batching = fatigue_level != "low"
    depth_control = "concise" if fatigue_level in ("moderate", "high") else "balanced"

    narrative = ""
    if minutes >= 120:
        narrative = (
            "You've been in deep operational debugging for several hours.\n\n"
            "I'll keep recommendations concise unless you ask for deeper replay analysis."
        )
    elif minutes >= 60:
        narrative = "You're in focused work — I'll batch recommendations and avoid low-value interruptions."
    else:
        narrative = "Attention load is manageable — full operational depth available on request."

    return {
        "ok": True,
        "phase": "10.1.4E",
        "fatigue_level": fatigue_level,
        "focus_minutes": minutes,
        "depth_control": depth_control,
        "recommendation_batching": recommendation_batching,
        "should_interrupt": calm.get("should_interrupt", True),
        "narrative": narrative,
        "features": {
            "fatigue_estimation": True,
            "interruption_timing": True,
            "investigation_depth_control": True,
            "recommendation_batching": True,
            "focus_recovery": minutes >= 90,
            "cognitive_load_awareness": True,
        },
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }
