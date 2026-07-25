# SPDX-License-Identifier: Apache-2.0
"""Live operational grounding aggregate — Phase 11.7.5."""

from __future__ import annotations

from typing import Any

from aethos_core.live_operational_grounding.grounding_runtime import orchestrate_live_grounding


def assess_live_operational_grounding(
    *,
    session_id: str = "default",
    channel: str = "chat",
    primary_subject: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Phase 11.7.5 — live operational grounding & provider reality validation."""
    if not primary_subject:
        try:
            from aethos_core.operational_context_memory.memory_precedence import reconcile_memory_layers

            primary_subject = reconcile_memory_layers(session_id=session_id, channel=channel).get("primary_subject")
        except Exception:
            pass

    live = orchestrate_live_grounding(
        session_id=session_id,
        channel=channel,
        primary_subject=primary_subject,
    )
    return {
        "ok": True,
        "phase": "11.7.5",
        "converged": live.get("live_grounding_qualified"),
        "live_operational_grounding": live,
        "summary": live.get("summary", "Live operational grounding assessing."),
    }
