# SPDX-License-Identifier: Apache-2.0
"""Emotional realism runtime — calm reassurance and honest humility."""

from __future__ import annotations

from time import time
from typing import Any


def assess_emotional_realism(*, session_id: str = "default", user_text: str | None = None) -> dict[str, Any]:
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity
    from aethos_core.presence.calm.calm_presence_runtime import get_calm_presence_state

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    calm = get_calm_presence_state(session_id=session_id)
    focus_minutes = float(calm.get("focus_minutes") or 0)

    frustration_signals = bool(user_text and any(w in user_text.lower() for w in ("again", "still broken", "frustrated", "why won't")))
    overload = focus_minutes >= 120 or calm.get("quiet_mode_recommended")

    tone_lines = []
    if record.get("resolved"):
        tone_lines.append(f"We made solid progress on **{record['resolved'][0].split(' caused')[0].split('Fixed ')[-1]}**.")
    if overload:
        tone_lines.append("You've been in deep operational work — I'll keep this concise and calm.")
    elif focus_minutes >= 60:
        tone_lines.append("Good momentum. I'll stay focused on what matters most.")
    else:
        tone_lines.append("I'm here to help you think clearly through the operational picture.")

    if frustration_signals:
        tone_lines.append("I'll slow down and walk through one validation step at a time.")

    return {
        "ok": True,
        "phase": "10.1.4D",
        "tone_narrative": "\n".join(tone_lines),
        "signals": {
            "frustration_detected": frustration_signals,
            "overload_detected": overload,
            "focus_minutes": focus_minutes,
        },
        "features": {
            "calm_reassurance": True,
            "frustration_detection": True,
            "overload_detection": True,
            "confidence_humility": True,
            "progress_acknowledgment": bool(record.get("resolved")),
            "collaboration_warmth": True,
        },
        "invariant": "Emotion supports clarity, not manipulation.",
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }
