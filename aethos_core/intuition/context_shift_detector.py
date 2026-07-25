# SPDX-License-Identifier: Apache-2.0
"""Context shift detector — detects changing operator focus."""

from __future__ import annotations

from typing import Any


def detect_context_shift(*, session_id: str = "default", user_text: str | None = None) -> dict[str, Any]:
    from aethos_core.human_centered.continuity_memory import load_continuity_memory
    from aethos_core.presence.live.live_presence_runtime import get_live_focus

    record = load_continuity_memory(session_id=session_id)
    live = get_live_focus(session_id=session_id)
    prior = record.get("current_system_focus") or record.get("focus") or ""
    current = live.get("topic") or ""
    text = (user_text or "").lower()

    shift = False
    new_focus = current
    if text:
        for keyword, label in (
            ("replay", "replay integrity"),
            ("route", "Human API convergence"),
            ("deploy", "deployment reliability"),
            ("living", "Living Intelligence"),
        ):
            if keyword in text:
                new_focus = label
                shift = label.lower() not in prior.lower()
                break

    return {
        "ok": True,
        "shift_detected": shift or bool(current and current != prior),
        "prior_focus": prior,
        "current_focus": new_focus or prior,
        "live_focus_minutes": live.get("duration_minutes"),
    }
