# SPDX-License-Identifier: Apache-2.0
"""Ambiguity scoring — detect when continuity inference may be wrong."""

from __future__ import annotations

from typing import Any

from aethos_core.continuity_reconstruction.subject_affinity import rank_operational_subjects


def score_continuity_ambiguity(
    *,
    user_text: str,
    bridge: dict[str, Any],
    intent: str | None = None,
) -> dict[str, Any]:
    ranked = rank_operational_subjects(user_text=user_text, bridge=bridge)
    if not ranked:
        return {"ambiguous": True, "ambiguity_score": 0.85, "reason": "no_operational_subjects"}

    top = ranked[0]["affinity_score"]
    second = ranked[1]["affinity_score"] if len(ranked) > 1 else 0.0
    margin = top - second

    ambiguous = False
    reasons: list[str] = []

    if len(ranked) >= 2 and margin < 0.35:
        ambiguous = True
        reasons.append("competing_subjects")
    if top < 0.75 and intent in {"implicit_followup", "situation_improved"}:
        ambiguous = True
        reasons.append("vague_prompt")
    if not bridge.get("has_memory"):
        ambiguous = True
        reasons.append("thin_memory")
    if len(bridge.get("active_investigations") or []) >= 2 and intent in {"implicit_followup", "situation_improved", "what_changed"}:
        ambiguous = True
        reasons.append("multi_investigation")
    if len(bridge.get("active_investigations") or []) >= 3 and margin < 0.5:
        ambiguous = True
        if "multi_investigation" not in reasons:
            reasons.append("multi_investigation")

    ambiguity_score = 0.2
    if ambiguous:
        ambiguity_score = min(0.95, 0.55 + (0.35 - min(margin, 0.35)))
    elif margin >= 0.75:
        ambiguity_score = 0.15

    return {
        "ambiguous": ambiguous,
        "ambiguity_score": round(ambiguity_score, 2),
        "margin": round(margin, 2),
        "top_subject": ranked[0],
        "alternatives": ranked[1:3],
        "reasons": reasons,
    }
