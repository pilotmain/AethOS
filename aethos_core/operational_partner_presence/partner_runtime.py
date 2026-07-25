# SPDX-License-Identifier: Apache-2.0
"""Partner runtime — investigation-aware operational companionship."""

from __future__ import annotations

from typing import Any

from aethos_core.continuity_reconstruction.thread_recovery import reconstruct_operational_thread
from aethos_core.operational_context_memory.context_bridge import build_operational_context_bridge


def build_partner_context(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    thread = reconstruct_operational_thread(session_id=session_id, channel=channel)
    bridge = build_operational_context_bridge(session_id=session_id, channel=channel)
    investigations = thread.get("active_investigations") or []
    return {
        **thread,
        "investigation_aware": bool(investigations or bridge.get("primary_subject")),
        "partner_mode": "operational_companion",
        "summary": "Operational partner presence active — investigation continuity preserved.",
    }


def assess_operational_partner_presence(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    partner = build_partner_context(session_id=session_id, channel=channel)
    return {"ok": True, **partner}
