# SPDX-License-Identifier: Apache-2.0
"""Cross-surface bridge — align Telegram, web chat, and Mission Control memory."""

from __future__ import annotations

from typing import Any


def merge_cross_surface_context(*, session_id: str = "default") -> dict[str, Any]:
    """Merge continuity signals from human-centered and relational memory layers."""
    surfaces: list[str] = []
    merged: dict[str, Any] = {"session_id": session_id, "surfaces": surfaces}

    try:
        from aethos_core.human_centered.continuity_memory import load_continuity_memory

        continuity = load_continuity_memory(session_id=session_id)
        if continuity.get("focus"):
            merged["mc_focus"] = continuity.get("focus")
            merged["mc_phase"] = continuity.get("phase")
            surfaces.append("mission_control")
    except Exception:
        pass

    try:
        from aethos_core.relational.conversational_memory import recent_context

        recent = recent_context(session_id=session_id, limit=4)
        if recent:
            merged["recent_turn_count"] = len(recent)
            surfaces.append("relational")
    except Exception:
        pass

    if session_id.startswith("tg-"):
        surfaces.append("telegram")

    merged["surfaces"] = list(dict.fromkeys(surfaces))
    merged["converged"] = len(surfaces) >= 2
    merged["summary"] = (
        f"Cross-surface continuity aligned across {', '.join(merged['surfaces']) or 'session'}."
        if merged["surfaces"]
        else "Cross-surface continuity thin — single-surface session."
    )
    return merged
