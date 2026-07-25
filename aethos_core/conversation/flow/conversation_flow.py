# SPDX-License-Identifier: Apache-2.0
"""Conversation flow — progressive disclosure and adaptive pacing."""

from __future__ import annotations

from typing import Any


def shape_progressive_response(
    *,
    short_summary: str,
    deep_detail: str | None = None,
    confidence: float = 0.65,
    offer_depth: bool = True,
) -> dict[str, Any]:
    """Short first — deeper on request."""
    lines = [short_summary.strip()]
    if confidence < 0.75:
        lines.append(f"Confidence is **{'moderate' if confidence >= 0.55 else 'limited'}** ({confidence:.2f}).")
    if offer_depth:
        lines.append("")
        lines.append("Want the quick explanation or full replay?")
    return {
        "ok": True,
        "phase": "short",
        "text": "\n".join(lines),
        "deep_detail": deep_detail,
        "progressive_disclosure": True,
        "autonomous_execution_blocked": True,
    }


def apply_conversation_flow(
    *,
    session_id: str = "default",
    core_text: str,
    confidence: float = 0.72,
    verbosity: str = "medium",
) -> str:
    """Adaptive verbosity and pacing."""
    from aethos_core.personal_intelligence.personal_runtime import get_personal_intelligence_status

    personal = get_personal_intelligence_status(session_id=session_id)
    style = (personal.get("profile") or {}).get("explanation_style", "balanced")

    if verbosity == "low" or style == "expert":
        parts = [p.strip() for p in core_text.split("\n\n") if p.strip()]
        return "\n\n".join(parts[:4]) + ("\n\n*(More detail available on request.)*" if len(parts) > 4 else "")

    if style == "beginner":
        return core_text + "\n\n*Ask if you'd like me to walk through any step.*"

    shaped = shape_progressive_response(
        short_summary=core_text.split("\n\n")[0] if core_text else core_text,
        deep_detail=core_text,
        confidence=confidence,
    )
    if verbosity == "high":
        return core_text
    return shaped.get("text", core_text)
