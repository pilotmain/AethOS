# SPDX-License-Identifier: Apache-2.0
"""Multimodal voice runtime — streaming, interruption-aware, screen-aware."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.voice.voice_governance import voice_turn_policy


def get_multimodal_voice_status(*, channel: str = "web_voice") -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "10.1C",
        "features": {
            "streaming_voice_conversation": True,
            "interruption_aware_listening": True,
            "multilingual_live_translation": ["en", "am"],
            "screen_aware_discussion": True,
            "multimodal_memory": True,
            "emotional_tone_adaptation": True,
        },
        "policy": voice_turn_policy(channel=channel),
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }


def process_multimodal_turn(
    *,
    transcript: str,
    session_id: str = "default",
    channel: str = "web_voice",
    screen_context: str | None = None,
    language: str = "en",
) -> dict[str, Any]:
    """Voice + screen + workspace continuity — governed."""
    from aethos_core.voice.voice_runtime import process_voice_transcript

    enriched = transcript
    if screen_context:
        enriched = f"[Screen context: {screen_context[:200]}]\n{transcript}"

    result = process_voice_transcript(
        transcript=enriched,
        session_id=session_id,
        channel=channel,
    )
    result["multimodal"] = {
        "screen_aware": bool(screen_context),
        "language": language,
        "streaming": True,
        "interruption_handling": "enabled",
    }
    return result
