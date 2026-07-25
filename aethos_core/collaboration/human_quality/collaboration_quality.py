# SPDX-License-Identifier: Apache-2.0
"""Collaboration human quality — acknowledgment, companionship, emotional realism."""

from __future__ import annotations

from typing import Any


def shape_collaborative_phrasing(
    *,
    resolved: list[str] | None = None,
    remaining: str | None = None,
    confidence: float = 0.72,
    telemetry_note: str | None = None,
) -> str:
    """Less robotic — shared progress awareness."""
    lines: list[str] = []
    if resolved:
        if len(resolved) == 1:
            lines.append(f"We stabilized **{resolved[0]}**.")
        else:
            lines.append("We stabilized:")
            for r in resolved[:3]:
                lines.append(f"- {r}")

    if remaining:
        lines.append("")
        lines.append(f"The remaining validation step is **{remaining}**.")

    if confidence < 0.8:
        note = telemetry_note or "telemetry freshness is still slightly degraded"
        lines.append("")
        lines.append(f"Confidence is improving, but {note}.")

    lines.append("")
    lines.append("*I'm here with you — bounded by evidence, never acting without governance.*")
    return "\n".join(lines)


def get_collaboration_quality(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    remaining = (record.get("pending_validation") or record.get("unresolved") or [None])[0]
    text = shape_collaborative_phrasing(
        resolved=record.get("resolved"),
        remaining=remaining,
        confidence=float(record.get("confidence") or 0.72),
    )
    return {
        "ok": True,
        "features": {
            "operator_acknowledgment": True,
            "collaborative_phrasing": True,
            "uncertainty_honesty": True,
            "investigation_companionship": True,
            "shared_progress_awareness": True,
            "emotional_realism": True,
        },
        "sample_phrasing": text,
        "autonomous_execution_blocked": True,
    }
