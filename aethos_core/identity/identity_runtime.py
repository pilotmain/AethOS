# SPDX-License-Identifier: Apache-2.0
"""Identity runtime — unified conversational identity orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.identity.conversational_restraint import (
    should_suppress_confidence_suffix,
    should_suppress_governance_footer,
)
from aethos_core.identity.governance_presence import apply_contextual_governance
from aethos_core.identity.response_alignment import align_legacy_phrasing
from aethos_core.identity.trust_language import CONFIDENCE_TRANSPARENCY


def build_identity_context(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.relational.conversational_memory import recent_context

    recent = recent_context(session_id=session_id)
    return {
        "session_id": session_id,
        "returning": len([t for t in recent if t.get("role") == "assistant"]) >= 1,
        "recent_turns": recent,
    }


def align_outbound_reply(
    reply: str,
    *,
    emotional_context: dict[str, Any] | None = None,
    intent: str | None = None,
    lane: str | None = None,
    include_governance_footer: bool = True,
) -> str:
    """Apply identity convergence: legacy cleanup, restraint, contextual governance."""
    ctx = emotional_context or {}
    session_id = str(ctx.get("session_id") or "default")
    text = align_legacy_phrasing(reply)

    if ctx.get("confidence_transparency") and not should_suppress_confidence_suffix(intent=intent, text=text):
        text = f"{text.rstrip()}\n\n*{CONFIDENCE_TRANSPARENCY}*"

    suppress = should_suppress_governance_footer(intent=intent, session_id=session_id)
    if suppress or ctx.get("suppress_governance_footer"):
        include_governance_footer = False

    text = apply_contextual_governance(
        text,
        intent=intent,
        lane=lane,
        emotional_context=ctx,
        include_governance=include_governance_footer,
    )
    return align_legacy_phrasing(text)
