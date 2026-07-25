# SPDX-License-Identifier: Apache-2.0
"""Operational thread integrity aggregate — Phase 11.7.2."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_thread_integrity.thread_integrity_runtime import assess_operational_thread_integrity as _assess_integrity


def assess_operational_thread_integrity(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    """Phase 11.7.2 — operational thread integrity."""
    from aethos_core.continuity_reconstruction.thread_recovery import reconstruct_operational_thread
    from aethos_core.operational_context_memory.context_bridge import build_operational_context_bridge

    bridge = build_operational_context_bridge(session_id=session_id, channel=channel)
    thread = reconstruct_operational_thread(session_id=session_id, channel=channel)
    integrity = _assess_integrity(session_id=session_id, channel=channel, bridge=bridge)

    return {
        "ok": True,
        "phase": "11.7.2",
        "converged": integrity.get("integrity_qualified"),
        "operational_thread": thread,
        "thread_integrity": integrity,
        "summary": integrity.get("summary", "Operational thread integrity assessing."),
    }
