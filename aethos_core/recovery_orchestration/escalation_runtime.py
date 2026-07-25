# SPDX-License-Identifier: Apache-2.0
"""Escalation runtime — confidence-aware escalation."""

from __future__ import annotations

from typing import Any


def assess_escalation(*, decay: dict[str, Any], restart_loops: int) -> dict[str, Any]:
    escalate = restart_loops >= 2 or decay.get("verification_decay", 0) >= 0.2
    level = "critical" if restart_loops >= 3 else "elevated" if escalate else "normal"
    return {
        "escalation_level": level,
        "escalate": escalate,
        "summary": f"Escalation level: {level}." if escalate else "No escalation required.",
    }
