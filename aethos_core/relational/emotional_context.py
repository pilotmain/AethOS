# SPDX-License-Identifier: Apache-2.0
"""Emotional context — conversational emotional awareness."""

from __future__ import annotations

from typing import Any

from aethos_core.relational.collaboration_modes import select_collaboration_mode
from aethos_core.relational.human_signal_detection import detect_human_signals


def build_emotional_context(
    *,
    user_text: str | None = None,
    session_id: str = "default",
    channel: str = "chat",
    operational_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build emotional/relational context for a turn."""
    from aethos_core.relational.operator_style import get_operator_style
    from aethos_core.relational.trust_memory import recall_trust_preferences

    style = get_operator_style(session_id=session_id)
    prefs = recall_trust_preferences(session_id=session_id)
    mode = select_collaboration_mode(
        user_text,
        operator_preference=style.get("preferred_mode"),
        operational_context=operational_context,
    )
    signals = detect_human_signals(user_text)

    guidance: list[str] = []
    if signals.get("frustrated"):
        guidance.extend(["Use calmer tone", "Reduce verbosity", "Increase confidence transparency", "Fewer interruptions"])
    if signals.get("urgent"):
        guidance.append("Lead with actionable next steps")
    if mode.get("mode") == "crisis":
        guidance.append("Operational clarity over exploration")

    return {
        "session_id": session_id,
        "channel": channel,
        "signals": signals,
        "mode": mode,
        "style": style,
        "preferences": prefs,
        "guidance": guidance,
        "confidence_transparency": signals.get("frustrated") or mode.get("mode") == "crisis",
    }
