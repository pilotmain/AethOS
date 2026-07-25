# SPDX-License-Identifier: Apache-2.0
"""Explainability envelope — wrap intelligent conclusions with rationale."""

from __future__ import annotations

from typing import Any


def wrap_with_explainability(
    *,
    conclusion: str,
    confidence: float | None = None,
    reasons: list[str] | None = None,
    evidence_sources: list[str] | None = None,
    missing_evidence: list[str] | None = None,
    replay_trace: str | None = None,
) -> dict[str, Any]:
    """Every intelligent conclusion explains itself."""
    rationale_parts: list[str] = []
    if reasons:
        rationale_parts.append("**Why:** " + "; ".join(reasons[:4]))
    if confidence is not None:
        rationale_parts.append(f"**Confidence:** {confidence:.2f}")
        if confidence < 0.7 and missing_evidence:
            rationale_parts.append(f"**Confidence lowered due to:** {'; '.join(missing_evidence[:3])}")
    if evidence_sources:
        rationale_parts.append("**Evidence lineage:** " + ", ".join(evidence_sources[:4]))
    if missing_evidence and confidence is None:
        rationale_parts.append("**Missing evidence:** " + ", ".join(missing_evidence[:4]))
    if replay_trace:
        rationale_parts.append(f"**Replay trace:** {replay_trace[:200]}")

    envelope = "\n".join(rationale_parts)
    return {
        "ok": True,
        "conclusion": conclusion,
        "explainability": envelope,
        "full_text": conclusion + ("\n\n" + envelope if envelope else ""),
        "confidence": confidence,
        "readonly": True,
        "autonomous_execution_blocked": True,
    }
