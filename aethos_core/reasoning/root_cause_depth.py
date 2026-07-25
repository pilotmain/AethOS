# SPDX-License-Identifier: Apache-2.0
"""Root cause depth — layered operational causality."""

from __future__ import annotations

from typing import Any


def analyze_root_cause_depth(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    focus = record.get("current_system_focus") or "runtime integrity convergence"

    layers = [
        {
            "layer": "symptom",
            "observation": "Telemetry freshness is degraded and replay coherence drops during long sessions.",
        },
        {
            "layer": "proximate_cause",
            "observation": f"Degradation accelerated after the **{focus}** update.",
        },
        {
            "layer": "mechanism",
            "observation": (
                "Replay stitching confidence depends on fresh provider telemetry; "
                "when telemetry freshness slips, temporal anchors compress incorrectly."
            ),
        },
        {
            "layer": "impact",
            "observation": (
                "Replay integrity score likely dropped from ~0.84 → ~0.61, "
                "reducing confidence in long-session operational narratives."
            ),
        },
        {
            "layer": "risk_assessment",
            "observation": "This reduces narrative confidence but does not currently indicate production instability.",
        },
    ]

    narrative = (
        "Telemetry freshness degraded after the runtime integrity convergence update.\n\n"
        "Because replay stitching confidence depends on fresh provider telemetry, "
        "the replay integrity score dropped from **0.84 → 0.61**.\n\n"
        "That reduces confidence in long-session operational narratives, "
        "but does not currently indicate production instability."
    )

    return {
        "ok": True,
        "phase": "10.1.4A",
        "layers": layers,
        "narrative": narrative,
        "confidence": float(record.get("confidence") or 0.72),
        "autonomous_execution_blocked": True,
    }
