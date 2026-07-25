# SPDX-License-Identifier: Apache-2.0
"""Living companion runtime — Phase 10.1 convergence orchestrator."""

from __future__ import annotations

from time import time
from typing import Any


def get_living_companion_overview(*, session_id: str = "default") -> dict[str, Any]:
    """Unified Phase 10.1 living intelligence state."""
    from aethos_core.collaboration.teamwork_runtime import list_collaboration_rooms
    from aethos_core.conversation.conversation_runtime import get_conversation_status
    from aethos_core.copilot.copilot_runtime import get_copilot_status
    from aethos_core.human_centered.human_os_runtime import get_human_os_overview
    from aethos_core.human_centered.thinking_boundaries import assess_thinking_boundaries
    from aethos_core.personal_intelligence.personal_runtime import get_personal_intelligence_status
    from aethos_core.presence.live.live_presence_runtime import get_live_presence_status, get_live_operational_stream
    from aethos_core.trust.world_class_explainability import build_world_class_explanation
    from aethos_core.voice.multimodal_runtime import get_multimodal_voice_status

    base = get_human_os_overview(session_id=session_id)
    return {
        **base,
        "phase": "10.1.4",
        "identity": "living operational companion",
        "mission": "continuously present, deeply collaborative, impossibly capable — without losing trust",
        "live_presence": get_live_presence_status(session_id=session_id),
        "live_stream": get_live_operational_stream(session_id=session_id, limit=8),
        "conversation": get_conversation_status(session_id=session_id),
        "multimodal_voice": get_multimodal_voice_status(),
        "copilot": get_copilot_status(session_id=session_id),
        "personal_intelligence": get_personal_intelligence_status(session_id=session_id),
        "thinking_boundaries": assess_thinking_boundaries(),
        "world_class_trust": build_world_class_explanation(session_id=session_id),
        "teamwork": list_collaboration_rooms(operator_id=session_id),
        "impossible_feeling": {
            "reaction_target": "How is this system this helpful, this aware, this capable, and still this trustworthy?",
            "positioning": "governed operational companion OS",
        },
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }
