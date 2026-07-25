# SPDX-License-Identifier: Apache-2.0
"""Companion narrative — operational arcs and strategic awareness."""

from __future__ import annotations

from time import time
from typing import Any


def build_companion_narrative(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)

    arc = {
        "from": "operational governance infrastructure",
        "to": "persistent human-centered operational companion",
        "phases": ["10.0", "10.1", "10.1.1", "10.1.2", "10.1.3", "10.1.4"],
    }

    milestones = [
        "Human-Centered Agentic OS foundation",
        "Living Intelligence runtime",
        "Human API convergence and runtime integrity",
        "Continuity memory realism",
        "Calm operational intelligence",
        "Operational depth and companion refinement",
    ]

    recurring = [
        "replay integrity during long-running sessions",
        "telemetry freshness and narrative coherence",
    ]

    narrative = (
        "Over the last several phases, AethOS evolved from:\n"
        "- operational governance infrastructure\n"
        "into:\n"
        "- a persistent human-centered operational companion.\n\n"
        "The current maturity focus is:\n"
        "**presence realism and replay integrity**."
    )

    return {
        "ok": True,
        "phase": "10.1.4F",
        "narrative": narrative,
        "operational_arc": arc,
        "milestones": milestones,
        "recurring_challenges": recurring,
        "current_focus": record.get("current_system_focus") or "presence realism and replay integrity",
        "system_maturity": "companion_intelligence_refinement",
        "features": {
            "operational_arcs": True,
            "milestone_awareness": True,
            "recurring_challenge_detection": True,
            "system_maturity_tracking": True,
            "narrative_continuity": True,
            "strategic_awareness": True,
        },
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }
