# SPDX-License-Identifier: Apache-2.0
"""Uncertainty reasoning — explain ambiguity honestly."""

from __future__ import annotations

from typing import Any


def explain_operational_uncertainty(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    confidence = float(record.get("confidence") or 0.72)

    unknowns = [
        "Whether replay stitching loss is corruption or expected compression artifact",
        "Exact scheduler cycle threshold where coherence degrades",
        "Whether telemetry freshness alone explains the integrity drop",
    ]

    narrative = (
        "I don't yet have enough evidence to call this a replay corruption issue. "
        "The pattern is consistent with compression-related temporal drift, "
        "but we need before/after scheduler cycle comparison to confirm."
    )

    return {
        "ok": True,
        "phase": "10.1.4A",
        "confidence": confidence,
        "confidence_label": "moderate" if confidence >= 0.55 else "limited",
        "unknowns": unknowns,
        "narrative": narrative,
        "autonomous_execution_blocked": True,
    }
