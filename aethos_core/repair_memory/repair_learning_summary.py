# SPDX-License-Identifier: Apache-2.0
"""Repair learning summaries for Mission Control and chat meta."""

from __future__ import annotations

from typing import Any

from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome


def repair_learning_summary(outcome: RepairAttemptOutcome) -> dict[str, Any]:
    recommended = (
        "Inspect deeper failure evidence before repeating the mutation."
        if not outcome.helped
        else "Continue monitoring recovery and confirm with fresh logs."
    )
    return {
        "title": "Repair learning",
        "operation": outcome.operation,
        "target": outcome.target,
        "result": outcome.result,
        "helped": outcome.helped,
        "health_after": outcome.health_after,
        "lesson": outcome.lesson,
        "recommended_next_action": recommended,
        "avoid_repeat_restart": not outcome.helped and outcome.operation == "restart",
        "evidence": list(outcome.evidence),
        "attempted_at": outcome.attempted_at,
    }


def format_repair_learning_lines(outcome: RepairAttemptOutcome) -> list[str]:
    summary = repair_learning_summary(outcome)
    lines = [
        "**Repair learning**",
        f"- Operation: **{summary['operation'].replace('_', ' ')}** attempted",
    ]
    if outcome.helped:
        lines.append("- Result: **helped / resolved**")
    else:
        lines.append("- Result: **did not resolve**")
    lines.append(f"- Lesson: {outcome.lesson}")
    if summary["avoid_repeat_restart"]:
        lines.append("- Recommended next action: inspect deeper evidence")
        lines.append("- Avoid repeat restart until root cause confirmed")
    return lines
