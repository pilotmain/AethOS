# SPDX-License-Identifier: Apache-2.0
"""Ambient presence — continuous operational collaborator."""

from __future__ import annotations

from time import time
from typing import Any


def build_while_you_were_away(*, window_hours: int = 8, session_id: str = "default") -> dict[str, Any]:
    """Passive monitoring summary — readonly awareness."""
    from aethos_core.presence.presence_runtime import run_presence_cycle, synthesize_operational_brief

    run_presence_cycle(session_id=session_id, channel="ambient")
    brief = synthesize_operational_brief(window_hours=window_hours, session_id=session_id)
    return {
        "ok": True,
        "title": "While you were away",
        "window_hours": window_hours,
        "brief": brief,
        "interruption_budget": 3,
        "passive_monitoring": True,
        "autonomous_execution_blocked": True,
        "generated_at": time(),
    }


def get_ambient_presence_status(*, session_id: str = "default") -> dict[str, Any]:
    return {
        "ok": True,
        "features": {
            "passive_monitoring": True,
            "while_you_were_away": True,
            "focus_sessions": True,
            "interruption_budgeting": True,
            "contextual_memory": True,
            "pattern_detection": True,
        },
        "session_id": session_id,
        "autonomous_execution_blocked": True,
    }
