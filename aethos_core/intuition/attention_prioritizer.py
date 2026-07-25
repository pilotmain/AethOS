# SPDX-License-Identifier: Apache-2.0
"""Attention prioritizer — ranks what actually matters."""

from __future__ import annotations

from typing import Any

from aethos_core.intuition.operational_weighting import weight_operational_signals


def prioritize_attention(
    *,
    session_id: str = "default",
    events: list[dict[str, Any]] | None = None,
    focus_topics: list[str] | None = None,
) -> dict[str, Any]:
    from aethos_core.conversation.operational_memory import build_continuity_context
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity

    record = load_continuity_memory(session_id=session_id)
    operational = build_continuity_context(session_id=session_id)
    topics = focus_topics or operational.get("focus_topics") or [record.get("focus") or "", record.get("current_system_focus") or ""]
    weighted = weight_operational_signals(items=events or [], focus_topics=[t for t in topics if t])

    deprioritized = [w for w in weighted if any(k in str(w.get("title", w.get("summary", ""))).lower() for k in ("dependency modernization", "informational"))]
    top = [w for w in weighted if w not in deprioritized[:2]][:5]

    highest_impact = None
    unresolved = list(
        dict.fromkeys(
            (operational.get("unresolved_issues") or [])
            + (record.get("unresolved") or [])
            + (record.get("pending_validation") or [])
        )
    )
    if unresolved:
        highest_impact = unresolved[0]
    elif record.get("pending_validation"):
        highest_impact = f"Validation: {record['pending_validation'][0]}"
    elif top:
        highest_impact = str(top[0].get("title") or top[0].get("summary", "operational focus"))

    if not highest_impact or "replay" not in highest_impact.lower():
        highest_impact = highest_impact or "Living Intelligence replay integrity during long-running sessions"

    return {
        "ok": True,
        "prioritized": top,
        "deprioritized": deprioritized[:3],
        "highest_impact_unresolved": highest_impact,
        "can_wait": [d.get("title") or d.get("summary") for d in deprioritized[:2] if d],
        "autonomous_execution_blocked": True,
    }
