# SPDX-License-Identifier: Apache-2.0
"""Living explainability — natural operational storytelling."""

from __future__ import annotations

from typing import Any


def build_living_explanation(
    *,
    session_id: str = "default",
    prioritized_over: str | None = None,
    because: list[str] | None = None,
) -> str:
    """Conversational explainability with trust narrative."""
    from aethos_core.human_centered.continuity_memory import load_continuity_memory

    record = load_continuity_memory(session_id=session_id)
    over = prioritized_over or "dependency modernization"
    focus = record.get("focus") or "runtime integrity"
    reasons = because or [
        f"unresolved {focus.lower()} issues affect current usability",
        "telemetry confidence is degraded",
        "modernization work is lower operational risk right now",
    ]
    lines = [
        f"I'm prioritizing **{focus}** over **{over}** because:",
    ]
    for r in reasons[:4]:
        lines.append(f"- {r}")
    return "\n".join(lines)


def get_living_explainability(*, session_id: str = "default") -> dict[str, Any]:
    narrative = build_living_explanation(session_id=session_id)
    return {
        "ok": True,
        "summary": narrative,
        "layered": {"summary": narrative.split("\n")[0], "detailed": narrative},
        "autonomous_execution_blocked": True,
    }
