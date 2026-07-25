# SPDX-License-Identifier: Apache-2.0
"""Investigation companion — collaborative debugging with honest limits."""

from __future__ import annotations

from time import time
from typing import Any


def build_investigation_companion_brief(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity
    from aethos_core.reasoning.uncertainty_reasoning import explain_operational_uncertainty

    from aethos_core.timeline.operational_timeline import _load_conversation_threads

    seed_default_continuity(session_id=session_id)
    record = load_continuity_memory(session_id=session_id)
    uncertainty = explain_operational_uncertainty(session_id=session_id)
    threads = _load_conversation_threads(session_id=session_id)

    resolved = record.get("resolved") or []
    unresolved = record.get("unresolved") or record.get("pending_validation") or []

    thread_topics: list[str] = []
    thread_unresolved: list[str] = []
    for thread in threads[:3]:
        thread_topics.extend(thread.get("topics") or [])
        thread_unresolved.extend(thread.get("unresolved") or [])
    if thread_unresolved:
        unresolved = list(dict.fromkeys(thread_unresolved + unresolved))

    checkpoints = []
    if resolved:
        checkpoints.append({"status": "resolved", "item": resolved[0]})
    if unresolved:
        checkpoints.append({"status": "investigating", "item": unresolved[0]})

    narrative_lines = []
    if resolved:
        narrative_lines.append(f"We stabilized the **{resolved[0].split(' caused')[0].split('Fixed ')[-1]}** earlier.")
    if thread_topics:
        narrative_lines.append("")
        narrative_lines.append("We were investigating:")
        for topic in list(dict.fromkeys(thread_topics))[:4]:
            narrative_lines.append(f"- {topic}")
    if unresolved:
        narrative_lines.append(
            f"The remaining instability appears isolated to **{unresolved[0].lower()}**."
        )
    narrative_lines.append("")
    narrative_lines.append(uncertainty.get("narrative", ""))
    narrative_lines.append("")
    narrative_lines.append(
        "The next best validation step is comparing replay continuity "
        "before and after scheduler cycles."
    )

    return {
        "ok": True,
        "phase": "10.1.4B",
        "narrative": "\n".join(narrative_lines),
        "checkpoints": checkpoints,
        "shared_progress": resolved[:3],
        "remaining": unresolved[:3],
        "next_validation": "Compare replay continuity before and after scheduler cycles",
        "uncertainty": uncertainty,
        "features": {
            "investigation_companionship": True,
            "shared_progress_tracking": True,
            "operational_checkpoints": True,
            "uncertainty_transparency": True,
            "investigation_momentum": True,
            "fatigue_aware_collaboration": True,
        },
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }
