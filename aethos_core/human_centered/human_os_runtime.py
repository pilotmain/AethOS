# SPDX-License-Identifier: Apache-2.0
"""Human-centered OS — convergence orchestrator."""

from __future__ import annotations

from time import time
from typing import Any


def get_human_os_overview(*, session_id: str = "default") -> dict[str, Any]:
    """Unified Phase 10.0 convergence state."""
    from aethos_core.action_runtime.action_runtime import list_pending_actions
    from aethos_core.channels.universal.universal_channel_runtime import list_universal_channels
    from aethos_core.collaboration.collaboration_runtime import list_collaboration_sessions
    from aethos_core.life.life_runtime import get_lifeos_status
    from aethos_core.presence.ambient_presence import get_ambient_presence_status
    from aethos_core.relational.relational_runtime import get_relational_state
    from aethos_core.runtime.edge_runtime import get_edge_runtime_status
    from aethos_core.trust.trust_leadership import build_trust_center
    from aethos_core.voice.voice_runtime import get_voice_status
    from aethos_sdk.plugin_registry import list_plugins

    return {
        "ok": True,
        "phase": "10.0",
        "vision": "human-centered agentic operating system",
        "principle": "warm like Pi, capable governed tool loops, trustworthy like enterprise infrastructure",
        "relational": get_relational_state(session_id=session_id),
        "voice": get_voice_status(),
        "channels": list_universal_channels(),
        "lifeos": get_lifeos_status(session_id=session_id),
        "actions": list_pending_actions(session_id=session_id),
        "ambient": get_ambient_presence_status(session_id=session_id),
        "collaboration": list_collaboration_sessions(operator_id=session_id),
        "trust": build_trust_center(session_id=session_id),
        "marketplace": {"plugins": list_plugins(), "sandboxed": True, "permission_scoped": True},
        "mobile_edge": get_edge_runtime_status(),
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }
